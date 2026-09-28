import streamlit as st
import yt_dlp
import os
import tempfile

st.set_page_config(page_title="YouTube MP3 Downloader", page_icon="🎵")

st.title("🎵 YouTube → MP3 変換アプリ")
st.write("YouTubeのURLを入力して、音声ファイルをMP3形式でダウンロードできます。")

# URL入力欄
url = st.text_input("YouTubeのURLを入力してください", placeholder="https://www.youtube.com/watch?v=...")

if st.button("MP3に変換する", type="primary"):
    if not url.strip():
        st.warning("URLを入力してください。")
    else:
        status_text = st.empty()
        status_text.info("動画情報を取得し、変換を行っています...")
        
        try:
            # 一時フォルダを作成して処理（サーバーの容量を圧迫しないため）
            with tempfile.TemporaryDirectory() as tmpdir:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    title = info.get('title', 'downloaded_audio')

                # 生成されたMP3ファイルを特定
                downloaded_files = [f for f in os.listdir(tmpdir) if f.endswith('.mp3')]

                if downloaded_files:
                    file_path = os.path.join(tmpdir, downloaded_files[0])
                    
                    with open(file_path, "rb") as f:
                        file_bytes = f.read()
                        
                    status_text.success("変換が完了しました！")
                    
                    # ダウンロードボタンの表示
                    st.download_button(
                        label="💾 MP3ファイルを保存",
                        data=file_bytes,
                        file_name=f"{title}.mp3",
                        mime="audio/mpeg"
                    )
                else:
                    status_text.error("MP3ファイルの生成に失敗しました。")

        except Exception as e:
            status_text.error(f"エラーが発生しました: {e}")
