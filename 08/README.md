# VM Translator（nand2tetris 第 7 + 8 章）

國立金門大學計算機結構第 11 週作業：將 Jack 編譯器產生的 VM（Virtual Machine） bytecode 翻譯成 Hack 組合語言。

## 一、VM 架構簡介

VM 是一座介於高階語言（Jack）與 Hack 平台之間的抽象機器，採用**堆疊式架構**：所有運算都先將運元推入堆疊，再進行運算並把結果放回堆疊。

### 記憶體模型

| 區段 | 實際對應 | 說明 |
|---|---|---|
| `constant` | 立即值 | 只可 push，值直接寫入指令 |
| `local` | `LCL` | 函式的區域變數 |
| `argument` | `ARG` | 函式的參數 |
| `this` | `THIS` | 目前物件的欄位 |
| `that` | `THAT` | 被呼叫物件的欄位 |
| `temp` | `RAM[5..12]` | 固定 8 個暫存槽 |
| `pointer` | `THIS` / `THAT` | index 0 → THIS，1 → THAT |
| `static` | `filename.index` | 每個 .vm 檔獨立的靜態變數 |

### 暫存器配置（Hack）

| 暫存器 | 用途 |
|---|---|
| `SP` (`RAM[0]`) | 堆疊指標，初始為 256 |
| `LCL` (`RAM[1]`) | 區域變數基底 |
| `ARG` (`RAM[2]`) | 參數基底 |
| `THIS` (`RAM[3]`) | this 基底 |
| `THAT` (`RAM[4]`) | that 基底 |
| `R13` | pop 時暫存目標位址 |
| `R14` | return 時暫存 FRAME |
| `R15` | return 時暫存返回位址 RET |

## 二、支援的 VM 指令

### 第 7 章：算術、邏輯與記憶體存取

- 算術邏輯（9 種）：`add`、`sub`、`neg`、`eq`、`gt`、`lt`、`and`、`or`、`not`
- 記憶體存取：`push <segment> <index>`、`pop <segment> <index>`，覆蓋上述 8 個區段
  - `eq/gt/lt` 使用 `D;JEQ`、`D;JGT`、`D;JLT` 搭配唯一標籤產生 true(-1) / false(0)
  - 二元運算使用 Hack 合法 mnemonics：`D+M`、`M-D`、`D&M`、`D|M`（不可寫成 `M+D` / `M&D` / `M|D`， assembler 不接受）

### 第 8 章：流程控制與函式呼叫

- 流程控制：`label`、`goto`、`if-goto`
  - label 會自動加上目前函式前綴，格式 `functionName$label`，避免不同函式的同名標籤衝突
- 函式協議：`function <name> <nVars>`、`call <name> <nArgs>`、`return`
  - `function`：宣告標籤並將 nVars 個區域變數初始化為 0
  - `call`：依序 push 返回位址、LCL、ARG、THIS、THAT，再設定 `ARG = SP - 5 - nArgs`、`LCL = SP`，最後跳轉到函式
  - `return`：以 `R14 = FRAME = LCL`、`R15 = RET = *(FRAME-5)`，依序歸還回傳值、`SP = ARG + 1`、回復 THAT/THIS/ARG/LCL，再跳回 RET

### Bootstrap Code

當輸入為**目錄**且目錄中包含 `Sys.vm` 時，會在程式最前面自動產生：

```
SP = 256
call Sys.init 0
```

單一 `.vm` 檔案輸入時不會加入 Bootstrap（測試腳本通常會自行設定 SP 與指標）。

## 三、執行方式

```bash
# 單一檔案：輸出同目錄同名 .asm
python vm2asm.py 07/StackArithmetic/SimpleAdd/SimpleAdd.vm

# 整個目錄：合併所有 .vm，輸出 <目錄名>.asm
python vm2asm.py 08/FunctionCalls/FibonacciElement
```

程式會自動：
- 移除 `//` 註解與空白行
- 依 .vm 主檔名產生 `static` 變數符號（例如 `Sys.0`）
- 依目錄中是否包含 `Sys.vm` 決定是否加入 Bootstrap

## 四、測試結果

已批次翻譯官方測資並用 Nand2Tetris `CPUEmulator` 搭配 `.tst` / `.cmp` 驗證，11 項全部通過：

| 章節 | 測資 | 結果 |
|---|---|---|
| 07 StackArithmetic | SimpleAdd、StackTest | PASS |
| 07 MemoryAccess | BasicTest、PointerTest、StaticTest | PASS |
| 08 ProgramFlow | BasicLoop、FibonacciSeries | PASS |
| 08 FunctionCalls | SimpleFunction、FibonacciElement、NestedCall、StaticsTest | PASS |

翻譯後的 `.asm` 也已用第 6 章 Hack 組譯器驗證，11 個檔案皆可正確組譯，無非法 mnemonic。
