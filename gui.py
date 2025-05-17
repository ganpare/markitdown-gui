import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from markitdown import MarkItDown
import os
from typing import List, Tuple
import threading
import queue


class MarkItDownGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MarkItDown Converter")

        # メインフレーム
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 変換モード選択
        self.mode_frame = ttk.LabelFrame(self.main_frame, text="変換モード", padding="5")
        self.mode_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        self.mode = tk.StringVar(value="file")
        ttk.Radiobutton(
            self.mode_frame,
            text="単一ファイル",
            variable=self.mode,
            value="file",
            command=self.update_ui,
        ).grid(row=0, column=0, padx=10)
        ttk.Radiobutton(
            self.mode_frame,
            text="フォルダ一括処理",
            variable=self.mode,
            value="folder",
            command=self.update_ui,
        ).grid(row=0, column=1, padx=10)

        # 入力選択
        self.input_frame = ttk.LabelFrame(self.main_frame, text="入力", padding="5")
        self.input_frame.grid(
            row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5
        )

        self.input_path = tk.StringVar()
        self.input_entry = ttk.Entry(
            self.input_frame, textvariable=self.input_path, width=60
        )
        self.input_entry.grid(row=0, column=0, padx=5)
        self.browse_input_btn = ttk.Button(
            self.input_frame, text="参照", command=self.select_input, width=10
        )
        self.browse_input_btn.grid(row=0, column=1, padx=5)

        # 出力ファイル選択（ファイルモード用）
        self.output_frame = ttk.LabelFrame(self.main_frame, text="出力", padding="5")
        self.output_frame.grid(
            row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5
        )

        self.output_path = tk.StringVar()
        self.output_entry = ttk.Entry(
            self.output_frame, textvariable=self.output_path, width=60
        )
        self.output_entry.grid(row=0, column=0, padx=5)
        self.browse_output_btn = ttk.Button(
            self.output_frame, text="参照", command=self.select_output_file, width=10
        )
        self.browse_output_btn.grid(row=0, column=1, padx=5)

        # 処理状況表示フレーム
        self.status_frame = ttk.LabelFrame(self.main_frame, text="処理状況", padding="5")
        self.status_frame.grid(
            row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5
        )

        # プログレスバー
        self.progress = ttk.Progressbar(self.status_frame, mode="determinate")
        self.progress.grid(
            row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5
        )

        # 詳細ステータス
        self.status_var = tk.StringVar(value="待機中...")
        self.status_label = ttk.Label(
            self.status_frame, textvariable=self.status_var, wraplength=400
        )
        self.status_label.grid(
            row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5
        )

        # カウンター表示
        self.counter_var = tk.StringVar(value="")
        self.counter_label = ttk.Label(self.status_frame, textvariable=self.counter_var)
        self.counter_label.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5
        )

        # 変換ボタン
        self.convert_btn = ttk.Button(
            self.main_frame, text="変換開始", command=self.start_conversion
        )
        self.convert_btn.grid(row=4, column=0, columnspan=3, pady=10)

        # MarkItDownのインスタンス
        self.converter = MarkItDown()

        # 変換処理用のキュー
        self.queue = queue.Queue()

        self.update_ui()

    def update_ui(self):
        is_file_mode = self.mode.get() == "file"
        if is_file_mode:
            self.output_frame.grid()
        else:
            self.output_frame.grid_remove()

    def select_input(self):
        if self.mode.get() == "file":
            self.select_input_file()
        else:
            self.select_input_folder()

    def select_input_file(self):
        filetypes = [
            ("サポートされているファイル", "*.epub;*.pdf"),
            ("EPUBファイル", "*.epub"),
            ("PDFファイル", "*.pdf"),
            ("すべてのファイル", "*.*"),
        ]
        filename = filedialog.askopenfilename(title="変換するファイルを選択", filetypes=filetypes)
        if filename:
            self.input_path.set(filename)
            # 出力ファイル名を自動設定
            output_filename = os.path.splitext(filename)[0] + ".md"
            self.output_path.set(output_filename)

    def select_input_folder(self):
        folder = filedialog.askdirectory(title="変換するファイルを含むフォルダを選択")
        if folder:
            self.input_path.set(folder)

    def select_output_file(self):
        filetypes = [("Markdownファイル", "*.md")]
        filename = filedialog.asksaveasfilename(
            title="出力先を選択", filetypes=filetypes, defaultextension=".md"
        )
        if filename:
            self.output_path.set(filename)

    def find_convertible_files(self, folder: str) -> List[str]:
        """指定フォルダ内の変換可能なファイルを検索します"""
        # PDFとEPUBファイルを別々に収集
        epub_files = {}  # ベースネーム: フルパス
        pdf_files = {}  # ベースネーム: フルパス

        for root, _, files in os.walk(folder):
            for file in files:
                lower_file = file.lower()
                if lower_file.endswith(".epub") or lower_file.endswith(".pdf"):
                    base_name = os.path.splitext(file)[0]
                    full_path = os.path.join(root, file)

                    if lower_file.endswith(".epub"):
                        epub_files[base_name] = full_path
                    else:  # .pdf
                        # EPUBがまだない場合のみPDFを追加
                        if base_name not in epub_files:
                            pdf_files[base_name] = full_path

        # EPUBファイルを優先して結果をまとめる
        convertible_files = list(epub_files.values()) + list(pdf_files.values())
        return sorted(convertible_files)  # パスでソートして安定した順序を保証

    def convert_file(self, input_file: str, output_file: str) -> Tuple[bool, str]:
        """ファイルを変換し、結果と詳細メッセージを返します"""
        try:
            # 出力ディレクトリが存在しない場合は作成
            output_dir = os.path.dirname(output_file)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            result = self.converter.convert(input_file)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result.text_content)
            return True, f"成功: {os.path.basename(input_file)}"
        except Exception as e:
            return False, f"エラー ({os.path.basename(input_file)}): {str(e)}"

    def start_conversion(self):
        """変換処理を別スレッドで開始します"""
        if not self.input_path.get():
            messagebox.showerror("エラー", "入力を選択してください。")
            return

        if self.mode.get() == "file" and not self.output_path.get():
            messagebox.showerror("エラー", "出力ファイルを選択してください。")
            return

        # UIコンポーネントを無効化
        self.convert_btn.state(["disabled"])
        self.browse_input_btn.state(["disabled"])
        self.browse_output_btn.state(["disabled"])

        # 変換処理を別スレッドで開始
        thread = threading.Thread(target=self.conversion_worker, daemon=True)
        thread.start()

        # 定期的に結果をチェック
        self.root.after(100, self.check_queue)

    def conversion_worker(self):
        """変換処理を実行するワーカースレッド"""
        if self.mode.get() == "file":
            # 単一ファイルモード
            self.progress["mode"] = "indeterminate"
            self.progress.start()
            success, message = self.convert_file(
                self.input_path.get(), self.output_path.get()
            )
            self.queue.put(("single", success, message))
        else:
            # フォルダモード
            input_folder = self.input_path.get()
            files = self.find_convertible_files(input_folder)

            if not files:
                self.queue.put(("folder", False, "変換可能なファイルが見つかりませんでした。"))
                return

            self.progress["mode"] = "determinate"
            self.progress["maximum"] = len(files)
            self.progress["value"] = 0

            success_count = 0
            error_messages = []

            for i, input_file in enumerate(files):
                output_file = os.path.splitext(input_file)[0] + ".md"
                if os.path.exists(output_file):
                    # すでに変換済みなのでスキップ
                    self.queue.put(
                        (
                            "progress",
                            i + 1,
                            len(files),
                            success_count,
                            f"スキップ: {os.path.basename(input_file)}",
                        )
                    )
                    continue
                # 変換処理
                success, message = self.convert_file(input_file, output_file)

                if success:
                    success_count += 1
                else:
                    error_messages.append(message)

                self.queue.put(("progress", i + 1, len(files), success_count, message))

    def check_queue(self):
        """キューから結果を取得して UI を更新"""
        try:
            while True:
                message = self.queue.get_nowait()
                if message[0] == "single":
                    # 単一ファイル変換の結果
                    self.progress.stop()
                    self.status_var.set(message[2])
                    if message[1]:  # success
                        messagebox.showinfo("完了", "変換が完了しました。")
                    self.conversion_complete()

                elif message[0] == "progress":
                    # フォルダ変換の進捗
                    _, current, total, success_count, status = message
                    self.progress["value"] = current
                    self.status_var.set(status)
                    self.counter_var.set(
                        f"処理済み: {current}/{total} (成功: {success_count})"
                    )

                    if current == total:
                        self.conversion_complete()
                        messagebox.showinfo(
                            "完了", f"{total}個中{success_count}個のファイルを変換しました。"
                        )

                self.queue.task_done()

        except queue.Empty:
            if self.convert_btn.instate(["disabled"]):
                self.root.after(100, self.check_queue)

    def conversion_complete(self):
        """変換完了時の処理"""
        self.convert_btn.state(["!disabled"])
        self.browse_input_btn.state(["!disabled"])
        self.browse_output_btn.state(["!disabled"])
        self.progress["value"] = 0
        self.status_var.set("待機中...")


def main():
    root = tk.Tk()
    app = MarkItDownGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
