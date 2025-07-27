import streamlit as st
import requests
import pandas as pd
import time
import random
from datetime import datetime
import io

# ページ設定
st.set_page_config(
    page_title="Note有料記事検索ツール",
    page_icon="📰",
    layout="wide"
)

# タイトル
st.title("📰 Note有料記事検索ツール")
st.markdown("note上の有料記事を「いいね数」順で検索します")

# デフォルトの除外ワード例
DEFAULT_EXCLUDE_WORDS = "稼ぐ,副業,収益,ビジネス,マネタイズ,集客"

# サイドバー
with st.sidebar:
    st.header("📋 使い方")
    st.info(
        "1. 検索キーワードを入力\n"
        "2. フィルターを選択\n"
        "3. 検索実行をクリック\n"
        "4. 結果をCSVでダウンロード"
    )
    
    st.header("⚠️ 注意事項")
    st.warning(
        "このツールは個人利用を前提としています。\n"
        "過度なアクセスは避けてください。"
    )

# メインコンテンツ
# 検索キーワード入力
search_query = st.text_input(
    "🔍 検索キーワード",
    placeholder="例: エッセイ、写真、小説、料理、旅行",
    help="検索したいキーワードを入力してください"
)

# 詳細設定
with st.expander("詳細設定"):
    col3, col4 = st.columns(2)
    
    with col3:
        pages = st.slider(
            "取得ページ数",
            min_value=1,
            max_value=20,
            value=10,
            help="1ページあたり20件取得します"
        )
        
        min_likes = st.number_input(
            "最低いいね数",
            min_value=0,
            value=0,
            step=10
        )
    
    with col4:
        price_max = st.number_input(
            "価格上限（円）",
            min_value=0,
            value=5000,
            step=100,
            help="0の場合は無制限"
        )

# 除外ワード設定
st.subheader("🚫 除外ワード設定")
exclude_words_input = st.text_area(
    "除外ワード（カンマ区切り）",
    value=DEFAULT_EXCLUDE_WORDS,
    placeholder="稼ぐ,副業,収益,ビジネス,マネタイズ,集客",
    help="除外したいワードをカンマで区切って入力してください"
)

# 除外ワードのリスト化
exclude_words = [w.strip() for w in exclude_words_input.split(",") if w.strip()]

# 適用される除外ワードを表示
if exclude_words:
    st.info(f"💡 適用される除外ワード: {', '.join(exclude_words)}")
else:
    st.warning("⚠️ 除外ワードが設定されていません")

# 検索実行ボタン
if st.button("🔍 検索実行", type="primary", use_container_width=True):
    if not search_query:
        st.error("検索キーワードを入力してください")
    else:
        # 進捗表示エリア
        progress_bar = st.progress(0)
        status_text = st.empty()
        results_container = st.container()
        
        all_articles = []
        
        try:
            # API呼び出し
            for page in range(pages):
                # 進捗更新
                progress = (page + 1) / pages
                progress_bar.progress(progress)
                status_text.text(f"検索中... {page + 1}/{pages} ページ")
                
                # APIエンドポイント
                url = "https://note.com/api/v3/searches"
                params = {
                    "context": "note",
                    "q": search_query,
                    "size": 20,
                    "start": page * 20
                }
                
                # リクエスト送信
                response = requests.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # 記事データの取得
                    articles = data.get("data", {}).get("notes", {}).get("contents", [])
                    
                    # 有料記事のフィルタリング
                    for article in articles:
                        try:
                            price = article.get("price", 0)
                            if price > 0:  # 有料記事のみ
                                # 除外ワードチェック（Noneを空文字列に変換）
                                title = str(article.get("name", "") or "")
                                description = str(article.get("description", "") or "")
                                text_to_check = f"{title} {description}".lower()
                                
                                excluded = False
                                for word in exclude_words:
                                    if word and word.lower() in text_to_check:
                                        excluded = True
                                        break
                                
                                if not excluded:
                                    # 追加フィルター
                                    like_count = article.get("like_count", 0)
                                    
                                    if like_count >= min_likes:
                                        if price_max == 0 or price <= price_max:
                                            # URLの構築（Noneチェック付き）
                                            user_data = article.get("user", {})
                                            urlname = user_data.get("urlname", "") if user_data else ""
                                            key = article.get("key", "")
                                            
                                            if urlname and key:  # URLに必要な情報がある場合のみ追加
                                                all_articles.append({
                                                    "likes": like_count,
                                                    "price": price,
                                                    "title": title,
                                                    "url": f"https://note.com/{urlname}/n/{key}",
                                                    "author_urlname": urlname,
                                                    "publish_at": str(article.get("publish_at", "") or ""),
                                                    "description_short": description[:100] if description else ""
                                                })
                        except Exception as e:
                            # 個別の記事でエラーが発生してもスキップして続行
                            continue
                
                else:
                    st.warning(f"ページ {page + 1} の取得に失敗しました: {response.status_code}")
                
                # レート制限対策
                time.sleep(random.uniform(0.8, 1.2))
            
            # 完了
            progress_bar.progress(1.0)
            status_text.text("検索完了！")
            
            if all_articles:
                # いいね数でソート
                all_articles.sort(key=lambda x: (x["likes"], x["publish_at"]), reverse=True)
                
                # DataFrameに変換
                df = pd.DataFrame(all_articles)
                
                # 結果表示
                with results_container:
                    st.success(f"✅ {len(all_articles)}件の有料記事が見つかりました")
                    
                    # CSV ダウンロードボタン
                    csv = df.to_csv(index=False, encoding='utf-8')
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                    
                    st.download_button(
                        label="📥 CSV形式でダウンロード",
                        data=csv,
                        file_name=f"note_paid_by_likes_{timestamp}.csv",
                        mime="text/csv"
                    )
                    
                    # テーブル表示（URLリンク付き）
                    st.dataframe(
                        df[["likes", "price", "title", "author_urlname", "publish_at", "url"]],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "likes": st.column_config.NumberColumn("いいね", format="%d"),
                            "price": st.column_config.NumberColumn("価格", format="¥%d"),
                            "title": st.column_config.TextColumn("タイトル"),
                            "author_urlname": st.column_config.TextColumn("著者"),
                            "publish_at": st.column_config.TextColumn("公開日"),
                            "url": st.column_config.LinkColumn("リンク", display_text="記事を読む")
                        }
                    )
            else:
                results_container.warning("条件に合う記事が見つかりませんでした")
                
        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")
            progress_bar.empty()
            status_text.empty()

# 詳細な使い方ガイド
st.markdown("---")
st.header("📖 詳しい使い方")

col_guide1, col_guide2 = st.columns(2)

with col_guide1:
    st.subheader("🔍 基本的な使い方")
    st.markdown("""
    **Step 1: キーワードを入力**
    - 探したいジャンルを入力してください
    - 例：「エッセイ」「写真」「小説」「料理」「旅行」など
    
    **Step 2: 除外ワードを設定**
    - デフォルトで一般的なビジネス系ワードが設定済み
    - 必要に応じて追加・削除・変更が可能
    - カンマ区切りで複数のワードを指定
    
    **Step 3: 検索実行**
    - 🔍ボタンをクリックして検索開始
    - 進捗バーで検索状況を確認
    
    **Step 4: 結果の確認**
    - いいね数の多い順に表示されます
    - CSV形式でダウンロード可能
    """)

with col_guide2:
    st.subheader("⚙️ 詳細設定の活用")
    st.markdown("""
    **取得ページ数**
    - 1ページ = 20記事
    - 10ページ = 200記事（推奨）
    - より多くの記事を調査したい場合は増やしてください
    
    **価格上限**
    - 高額な記事を除外したい場合に設定
    - 例：3000円以下の記事のみ表示
    
    **最低いいね数**
    - 人気度でフィルタリング
    - 例：100いいね以上の記事のみ表示
    
    **除外ワード**
    - デフォルトでビジネス系ワードが設定済み
    - 自由に編集・追加・削除が可能
    - カンマ区切りで複数指定可能
    - 例：「講座,教材,手法,アフィリエイト」
    """)

# 具体的な使用例
st.subheader("💡 具体的な使用例")

example_col1, example_col2, example_col3 = st.columns(3)

with example_col1:
    st.markdown("""
    **📝 エッセイを探す場合**
    - キーワード：「エッセイ」
    - 除外ワード：デフォルト + 「講座,教材」
    - 取得ページ数：10
    - 価格上限：3000円
    
    → 読みやすい価格帯の良質なエッセイが見つかります
    """)

with example_col2:
    st.markdown("""
    **📸 写真・画像系を探す場合**
    - キーワード：「写真」「イラスト」
    - 除外ワード：デフォルト + 「教室,スクール」
    - 最低いいね数：50
    
    → クリエイティブな作品に特化して検索
    """)

with example_col3:
    st.markdown("""
    **📚 小説・創作を探す場合**
    - キーワード：「小説」「創作」
    - 除外ワード：デフォルト + 「講座,教材,手法」
    - 価格上限：2000円
    
    → 純粋な創作作品のみを抽出
    """)

# 注意事項とコツ
st.subheader("⚠️ 使用時の注意とコツ")
st.markdown("""
**🔄 効率的な検索のコツ**
- まずはデフォルトの除外ワードで試してみる
- キーワードは具体的すぎず、広すぎず
- 結果が多すぎる場合は価格上限や最低いいね数で絞り込む
- 結果が少ない場合は除外ワードを減らしてみる

**📊 結果の見方**
- 「いいね」数が多い記事ほど読者の評価が高い
- 「価格」と「いいね」のバランスを見てコスパを判断
- 「リンク」列から直接記事を読むことが可能
- CSVにもURLが含まれるため、後で参照しやすい

**⏰ 検索時間について**
- 1ページあたり約1秒の間隔で取得（API制限のため）
- 10ページの場合、約10-15秒程度かかります
- 検索中はブラウザを閉じないでください
""")

# トラブルシューティング
st.subheader("🛠️ よくある問題と解決方法")
trouble_col1, trouble_col2 = st.columns(2)

with trouble_col1:
    st.markdown("""
    **Q: 検索結果が0件になる**
    - キーワードを変更してみる
    - 除外ワードを減らしてみる
    - 価格上限を上げる、または0にする
    - 最低いいね数を下げる
    """)

with trouble_col2:
    st.markdown("""
    **Q: 検索が途中で止まる**
    - しばらく待ってから再実行
    - 取得ページ数を減らす
    - ブラウザをリフレッシュして再試行
    """)

st.info("💡 このツールは note.com の非公式APIを使用しています。個人利用の範囲でご利用ください。")