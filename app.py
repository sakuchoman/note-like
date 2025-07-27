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

# フィルタープリセット定義
FILTER_PRESETS = {
    "ゆるめ": {
        "exclude_words": ["稼ぐ", "稼げる", "副業で月収", "収益化"],
        "price_max": None
    },
    "標準": {
        "exclude_words": ["稼", "副業", "収益", "ビジネス", "マネタイズ", "集客"],
        "price_max": 5000
    },
    "厳しめ": {
        "exclude_words": ["稼", "副業", "ビジネス", "収益", "集客", "マーケ", "売上", "コンサル", "セミナー"],
        "price_max": 3000
    },
    "カスタム": {
        "exclude_words": [],
        "price_max": None
    }
}

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
col1, col2 = st.columns([2, 1])

with col1:
    # 検索キーワード入力
    search_query = st.text_input(
        "検索キーワード",
        placeholder="例: エッセイ、写真、小説",
        help="検索したいキーワードを入力してください"
    )

with col2:
    # フィルタープリセット選択
    filter_preset = st.radio(
        "フィルタープリセット",
        options=list(FILTER_PRESETS.keys()),
        index=1,  # デフォルトは「標準」
        horizontal=True
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
            value=FILTER_PRESETS[filter_preset]["price_max"] or 10000,
            step=100,
            help="0の場合は無制限"
        )
        
    # カスタム除外ワード
    if filter_preset == "カスタム":
        custom_exclude = st.text_area(
            "除外ワード（カンマ区切り）",
            placeholder="稼ぐ,副業,ビジネス",
            help="除外したいワードをカンマで区切って入力"
        )
        exclude_words = [w.strip() for w in custom_exclude.split(",") if w.strip()]
    else:
        exclude_words = FILTER_PRESETS[filter_preset]["exclude_words"]
        st.info(f"除外ワード: {', '.join(exclude_words)}")

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
                        price = article.get("price", 0)
                        if price > 0:  # 有料記事のみ
                            # 除外ワードチェック
                            title = article.get("name", "")
                            description = article.get("description", "")
                            text_to_check = (title + " " + description).lower()
                            
                            excluded = False
                            for word in exclude_words:
                                if word.lower() in text_to_check:
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
                                                "publish_at": article.get("publish_at", ""),
                                                "description_short": description[:100] if description else ""
                                            })
                
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
                    
                    # テーブル表示
                    st.dataframe(
                        df[["likes", "price", "title", "author_urlname", "publish_at"]],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "likes": st.column_config.NumberColumn("いいね", format="%d"),
                            "price": st.column_config.NumberColumn("価格", format="¥%d"),
                            "title": st.column_config.TextColumn("タイトル"),
                            "author_urlname": st.column_config.TextColumn("著者"),
                            "publish_at": st.column_config.TextColumn("公開日")
                        }
                    )
            else:
                results_container.warning("条件に合う記事が見つかりませんでした")
                
        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")
            progress_bar.empty()
            status_text.empty()