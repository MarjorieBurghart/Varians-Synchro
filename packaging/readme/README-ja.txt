VARIANS-SYNCHRO {version} — すぐに使える版

このアーカイブには、Varians-Synchro と、その動作に必要なもの（Python、Qt）
がすべて含まれています。ほかに何もインストールする必要はありません。


インストールと起動
------------------
Windows（10 または 11、64 ビット）
  1. アーカイブ全体を展開します（右クリック →「すべて展開…」）。展開先は
     たとえば「ドキュメント」です。zip ファイルの中から直接 Varians-Synchro
     を起動しないでください。
  2. Varians-Synchro-{version} フォルダーの Varians-Synchro.exe をダブル
     クリックします。
  3. 初回起動：Varians-Synchro には署名がないため、Windows が「Windows に
     よって PC が保護されました」と表示することがあります。「詳細情報」を
     クリックし、「実行」をクリックしてください。ウイルス対策ソフトが起動前
     にプログラムを検査することもあります。
  デスクトップにショートカットを作るには：Varians-Synchro.exe を右クリック
  →「送る」→「デスクトップ (ショートカットを作成)」（Windows 11 では先に
  「その他のオプションを確認」）。

macOS（Apple シリコン搭載の Mac（M1、M2…）には「macos-arm64」、Intel 搭載
の Mac には「macos-x64」のアーカイブ）
  1. アーカイブをダブルクリックし、Varians-Synchro.app を「アプリケーション」
     フォルダーにドラッグします。
  2. 初回起動：Varians-Synchro は Apple の署名を受けていないため、macOS は
     開くことを拒否します（「Apple は検証できませんでした…」）。メッセージ
     を閉じ、「システム設定」→「プライバシーとセキュリティ」を開いて、下の
     ほうの Varians-Synchro についてのメッセージの横にある「このまま開く」
     をクリックし、確認します。macOS 14 以前では、Varians-Synchro.app を
     右クリック（または control キーを押しながらクリック）→「開く」→
     「開く」でも構いません。確認は最初の 1 回だけです。
  macOS が Varians-Synchro は「壊れている」と表示する場合は、ターミナルで
  次を入力します：
     xattr -dr com.apple.quarantine /Applications/Varians-Synchro.app

Linux（64 ビット x86。Ubuntu 22.04、Debian 12、Fedora 36 以降）
  1. アーカイブを展開：  unzip Varians-Synchro-{version}-linux-x64.zip
  2. 起動：              ./Varians-Synchro-{version}/Varians-Synchro
  Varians-Synchro は、どの Linux デスクトップにもあるグラフィックス・
  ライブラリ（OpenGL、libxcb、fontconfig）を使います。足りないものがあれば、
  たとえば Debian や Ubuntu では：
     sudo apt install libegl1 libgl1 libxcb1 libxkbcommon0 libfontconfig1


はじめての試用
--------------
Varians-Synchro の隣にある demo_local_ALTO フォルダーには、小さなサンプル
プロジェクト（exemple.vsynch：1 ページずつの証本 2 つと、その ALTO ファイル）
が入っています。このフォルダーをたとえば「ドキュメント」など別の場所に
コピーしてから exemple.vsynch を開き、ガイドの「2. はじめての試用：サンプル
プロジェクト」の節に従ってください。

Varians-Synchro は Varians 用のプロジェクトを準備します。Varians は別に
ダウンロードします：
  https://github.com/MarjorieBurghart/Varians/releases


更新
----
リリースのページから新しいアーカイブをダウンロードし、
  https://github.com/MarjorieBurghart/Varians-Synchro/releases
古いフォルダー（または Varians-Synchro.app）を新しいものと置き換えます。
プロジェクトと設定はこのフォルダーの中にはないので、そのまま残ります。

Varians-Synchro をアンインストールするには、このフォルダー（または
Varians-Synchro.app）を削除するだけです。


確認
----
アーカイブ：各アーカイブには SHA-256 のハッシュ値があります（リリースの
ページの .sha256 ファイル）。計算するには：
  Windows（PowerShell）：  Get-FileHash Varians-Synchro-{version}-windows-x64.zip
  macOS：                  shasum -a 256 Varians-Synchro-{version}-macos-arm64.zip
  Linux：                  sha256sum Varians-Synchro-{version}-linux-x64.zip

インストール：問題があるときは、Varians-Synchro が自分の翻訳、ヘルプ、
リソース、サンプルプロジェクト、Varians への書き出しを含む同期 1 件、
ウィンドウを自分で確認し、報告を書き出せます（数秒）：
  Windows（コマンド プロンプトで、Varians-Synchro のフォルダーにて）：
     start /wait Varians-Synchro.exe --self-test report.json
  macOS：
     /Applications/Varians-Synchro.app/Contents/MacOS/Varians-Synchro --self-test ~/report.json
  Linux：
     ./Varians-Synchro --self-test report.json
この報告を問題の報告に添付してください：
  https://github.com/MarjorieBurghart/Varians-Synchro/issues


ヘルプ
------
ガイドは Varians-Synchro の中にあります：「ユーザーガイドを開く」ボタン
(F1)。ウィンドウ上部で選んだ言語（「言語」）で表示されます。


構成要素
--------
Varians-Synchro には次のものが含まれます：Python（PSF ライセンス）、Qt と
PySide6（LGPL v3。差し替え可能な独立したライブラリ。ソースは
https://code.qt.io）、certifi（MPL 2.0）、Linux ではビルドに使ったシステム
のライブラリ（たとえば GLib、LGPL v2.1）。これらのライセンスの本文は
licences フォルダーにあります。
