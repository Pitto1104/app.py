
import streamlit as st
import yt_dlp
import os
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="YouTube MP3 Downloader", page_icon="🎵", layout="centered")

st.title("🎵 YouTube MP3 Downloader")
st.write("YouTubeの動画URLまたは**プレイリストURL**を入力してください。")

url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=... または playlist?list=...")

if st.button("MP3に変換・ダウンロード", type="primary"):
    if not url:
        st.warning("URLを入力してください。")
    else:
        status_text = st.empty()
        progress_bar = st.progress(0)
        status_text.text("🚀 処理を開始しています...")

        def download_single_video(target_url, output_dir):
            outtmpl_format = os.path.join(output_dir, '%(title)s - %(artist,uploader)s.%(ext)s')
            ydl_opts = {
                'format': 'ba/b',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '128',
                }],
                'postprocessor_args': {
                    'FFmpegExtractAudio': ['-threads', '2', '-q:a', '5']
                },
                'outtmpl': outtmpl_format,
                'quiet': True,
                'no_warnings': True,
                'writethumb': False,
                'writeinfojson': False,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['ios', 'android']
                    }
                },
                'nocheckcertificate': True,
                'ignoreerrors': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([target_url])

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                flat_opts = {
                    'extract_flat': 'in_playlist',
                    'quiet': True,
                    'skip_download': True,
                }
                with yt_dlp.YoutubeDL(flat_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                if info and 'entries' in info:
                    video_urls = [
                        f"https://www.youtube.com/watch?v={e['id']}" 
                        for e in info['entries'] if e and 'id' in e
                    ]
                else:
                    video_urls = [url]

                total_files = len(video_urls)
                completed_files = 0

                if total_files == 0:
                    st.error("動画情報を取得できませんでした。URLを確認してください。")
                else:
                    # 無料サーバーのメモリ溢れを防ぐため2並列に最適化
                    max_workers = min(2, total_files) if total_files > 1 else 1
                    
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        futures = [executor.submit(download_single_video, v_url, tmpdir) for v_url in video_urls]
                        
                        for future in as_completed(futures):
                            completed_files += 1
                            percent = completed_files / total_files
                            progress_bar.progress(percent)
                            status_text.text(f"⚡ 変換進行中: {completed_files} / {total_files} 曲完了 ({int(percent*100)}%)")

                    mp3_files = [
                        os.path.join(tmpdir, f) for f in os.listdir(tmpdir) 
                        if f.endswith('.mp3')
                    ]

                    status_text.empty()
                    progress_bar.empty()

                    if not mp3_files:
                        st.error("MP3ファイルの生成に失敗しました。動画の公開設定やURLをご確認ください。")
                    elif len(mp3_files) == 1:
                        file_name = os.path.basename(mp3_files[0])
                        st.success("🎉 完了しました！")
                        
                        with open(mp3_files[0], "rb") as f:
                            st.download_button(
                                label=f"💾 {file_name} を保存",
                                data=f.read(),
                                file_name=file_name,
                                mime="audio/mpeg"
                            )
                    else:
                        st.success(f"🎉 プレイリスト全 {len(mp3_files)} 曲の変換が完了しました！")
                        
                        with st.expander("🎵 変換された曲の一覧を確認する"):
                            for f in sorted(mp3_files):
                                st.write(f"- {os.path.basename(f)}")

                        zip_path = os.path.join(tmpdir, "playlist.zip")
                        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_STORED) as zipf:
                            for file in mp3_files:
                                zipf.write(file, os.path.basename(file))

                        with open(zip_path, "rb") as f:
                            st.download_button(
                                label="📦 MP3一括保存 (ZIPファイル)",
                                data=f.read(),
                                file_name="playlist_mp3s.zip",
                                mime="application/zip"
                            )

        except Exception as e:
            status_text.empty()
            progress_bar.empty()
            st.error(f"エラーが発生しました: {e}")
