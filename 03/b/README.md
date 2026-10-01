# Project 03/b：記憶體堆疊

計算機結構作業 03 (b)，使用 Nand2Tetris 的 HDL 語言實作大容量資料記憶體。三顆晶片全部沿用 03/a 的遞迴套路：**一層 DMux8Way 分送寫入訊號 + 8 個子記憶體 + 一層 Mux8Way16 收集輸出**，唯一差別在於位址要切幾段給下層。每題附 `.tst` 測試腳本與 `.cmp` 期望輸出，可用 Nand2Tetris 的 Hardware Simulator 驗證。

## 快速總覽

| 晶片 | 說明 | 容量 | 輸入 | 輸出 |
|------|------|------|------|------|
| RAM512.hdl | 512 個 16-bit 暫存器 | 8 × RAM64 | in[16], load, address[9] | out[16] |
| RAM4K.hdl | 4096 個 16-bit 暫存器 | 8 × RAM512 | in[16], load, address[12] | out[16] |
| RAM16K.hdl | 16384 個 16-bit 暫存器 | 8 × RAM4K | in[16], load, address[14] | out[16] |

## 實作順序（相依關係）

```
[ Project 03/a RAM64 ]
              │
              ▼
      1. RAM512
              │
              ▼
      2. RAM4K
              │
              ▼
      3. RAM16K  (Hack CPU 的資料記憶體)
```

三題的結構完全相同，差别只有「本層位址寬度 − 下層位址寬度」這件事：

| 晶片 | 位址寬度 | 本層選組位址 | 傳給下層的位址 |
|------|----------|--------------|----------------|
| RAM512 | 9 | `address[6..8]` | `address[0..5]` |
| RAM4K | 12 | `address[9..11]` | `address[0..8]` |
| RAM16K | 14 | `address[12..13]` | `address[0..11]` |

每層剛好從高 3 bit 切出來當選組訊號（8 選 1），剩下的低位段原封不動傳給 8 個子晶片。位址寬度每層固定增加 3 bit，容量就乘以 8：64 → 512 → 4K → 16K。

---

## 逐題解說

### 1. RAM512.hdl — 512 個 16-bit 暫存器
`address[9]` 切成兩段：
- **高 3 位 `address[6..8]`** 決定資料要寫進哪一個 RAM64（哪一組），交給 `DMux8Way` 分送 `load`。
- **低 6 位 `address[0..5]`** 決定該組內的第幾個位置，8 個 RAM64 共用同一組低位址。

8 組 × 每組 64 個 = 512，數量吻合。輸出用 `Mux8Way16` 依同一組高位址挑出。

```hdl
PARTS:
    DMux8Way(in=load, sel=address[6..8], a=load0, b=load1, c=load2, d=load3, e=load4, f=load5, g=load6, h=load7);
    RAM64(in=in, load=load0, address=address[0..5], out=r0);
    RAM64(in=in, load=load1, address=address[0..5], out=r1);
    // ... 一直到 r7
    RAM64(in=in, load=load7, address=address[0..5], out=r7);
    Mux8Way16(a=r0, b=r1, c=r2, d=r3, e=r4, f=r5, g=r6, h=r7, sel=address[6..8], out=out);
```

### 2. RAM4K.hdl — 4096 個 16-bit 暫存器
結構一模一樣，只把子晶片換成 RAM512、位址再多切 3 bit：
- **高 3 位 `address[9..11]`** 選組。
- **低 9 位 `address[0..8]`** 往下傳。

512 × 8 = 4096，容量正確。

```hdl
PARTS:
    DMux8Way(in=load, sel=address[9..11], a=load0, b=load1, c=load2, d=load3, e=load4, f=load5, g=load6, h=load7);
    RAM512(in=in, load=load0, address=address[0..8], out=r0);
    // ... 一直到 r7
    RAM512(in=in, load=load7, address=address[0..8], out=r7);
    Mux8Way16(a=r0, b=r1, c=r2, d=r3, e=r4, f=r5, g=r6, h=r7, sel=address[9..11], out=out);
```

### 3. RAM16K.hdl — 16384 個 16-bit 暫存器
Hack CPU 的完整資料記憶體，就是把 RAM4K 再堆一層。位址寬度 14 bit：
- **高 2 位 `address[12..13]`** 選組（`DMux8Way` 的 sel 只需 2 bit，多的會被忽略，語意上剛好是 4 選 1 的規模被放進 8 選 1 的接腳，恆為 0 的高 bit 不影響結果）。
- **低 12 位 `address[0..11]`** 傳給 8 個 RAM4K。

4K × 8 = 16K，符合 Hack 規格中最大資料記憶體的容量。

```hdl
PARTS:
    DMux8Way(in=load, sel=address[12..13], a=load0, b=load1, c=load2, d=load3, e=load4, f=load5, g=load6, h=load7);
    RAM4K(in=in, load=load0, address=address[0..11], out=r0);
    // ... 一直到 r7
    RAM4K(in=in, load=load7, address=address[0..11], out=r7);
    Mux8Way16(a=r0, b=r1, c=r2, d=r3, e=r4, f=r5, g=r6, h=r7, sel=address[12..13], out=out);
```

---

## 重點設計

- **統一模板**：所有 RAM 都是「`DMux8Way` 分送 load → 8 個子記憶體 → `Mux8Way16` 收集 out」，只有位址切片位置不同。
- **位址正交切分**：高 bit 選組、低 bit 選組內位置，兩段互不干擾，所以容量才會精確地乘以 8。
- **位址寬度與容量的關係**：`容量 = 2^(位址寬度)`，RAM16K 的 14 bit 位址剛好對應 16384 個位置。
- **寫入延遲一輪**：真正的儲存發生在下層的 Register/DFF，所以寫入值要到下一個時脈才出現在 `out`，這是所有 RAM 測試都會檢查的行為。
- **實作順序不可跳**：下層晶片若還是空模板，模擬器會讀到全 0，導致上層測試失敗，因此必須由 RAM64 逐層往上完成。
