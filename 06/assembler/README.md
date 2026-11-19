# Hack Assembler (Nand to Tetris Project 6)

以 Python 實作的 Hack 組譯器，遵循 Nand to Tetris 課程官方架構，將 `.asm` 檔組譯為 16-bit 的 `.hack` 機器碼。

## 專案結構

```text
nand2terris 的組譯器/
├── parser.py          # 讀取 .asm，去除註解與空白，提供解析介面
├── code_module.py     # dest / comp / jump 助記符轉二進位碼
├── symbol_table.py    # 預設符號、標籤與自訂變數管理
├── main.py            # 主程式，Two-Pass 掃描與輸出 .hack
├── test_assembler.py  # 驗證腳本
├── Add.asm            # 測試程式：R0 = 2 + 3
├── Max.asm            # 測試程式：R2 = max(R0, R1)
├── Add.hack           # Add.asm 的組譯結果
└── Max.hack           # Max.asm 的組譯結果
```

## 模組說明

### `parser.py`

- 移除 `//` 之後的註解與多餘空白
- 提供 `has_more_commands()`、`advance()`
- 提供 `command_type()`、`symbol()`、`dest()`、`comp()`、`jump()`

### `code_module.py`

- `dest()`：將 dest 助記符轉為 3-bit
- `comp()`：將 comp 助記符轉為 7-bit
- `jump()`：將 jump 助記符轉為 3-bit

### `symbol_table.py`

- 內建 `R0` 到 `R15`、`SP`、`LCL`、`ARG`、`THIS`、`THAT`、`SCREEN`、`KBD`
- 支援跳躍標籤
- 自訂變數從 RAM 位址 16 開始依序分配

### `main.py`

- 第一遍掃描：記錄所有 `(LABEL)` 標籤對應的 ROM 位址
- 第二遍掃描：產生 A-instruction 與 C-instruction 的 16-bit 機器碼

## 使用方式

組譯單一檔案：

```bash
python main.py Add.asm
```

輸出檔預設為同名的 `.hack` 檔，也可以指定輸出路徑：

```bash
python main.py Max.asm -o Max.hack
```

若系統沒有可用的 Python，可使用 `uv` 執行：

```bash
uv run --python 3.12 python main.py Add.asm
```

## 執行測試

```bash
python test_assembler.py
```

測試內容包含：

- `Add.asm` 輸出筆數、格式與機器碼內容
- `Max.asm` 輸出筆數、格式與機器碼內容
- 所有輸出皆為 16-bit 的 `0` / `1` 字串
- 預設符號與自訂符號表位址

預期結果：

```text
PASS Add.asm -> Add.hack (6 instructions, all 16-bit)
PASS Max.asm -> Max.hack (16 instructions, all 16-bit)
PASS symbol table predefined symbols and custom entry
All tests passed.
```

## 範例

`Add.asm`：

```asm
@2
D=A
@3
D=D+A
@0
M=D
```

組譯後的 `Add.hack`：

```text
0000000000000010
1110110000010000
0000000000000011
1110000010010000
0000000000000000
1110001100001000
```

## 支援的語法

- A-instruction：`@value`、`@symbol`
- C-instruction：`dest=comp;jump`，其中 `dest` 與 `jump` 可省略
- 標籤：`(LABEL)`
- 註解：`//` 之後的內容會被忽略
- 空白行會被忽略
