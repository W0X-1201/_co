# Project 03/a：位元儲存元件

計算機結構作業 03 (a)，使用 Nand2Tetris 的 HDL 語言實作一連串具備「記憶」能力的晶片：從 1-bit 的暫存器開始，一路堆疊成 16-bit 暫存器與多層記憶體陣列（RAM8、RAM64）。本單元的核心觀念是 **時序（sequential）** 與 **回饋（feedback）**：輸出不再是當下輸入的純函式，而是會被暫存在 DFF 中、下一個時脈才生效。每題附 `.tst` 測試腳本與 `.cmp` 期望輸出，可用 Nand2Tetris 的 Hardware Simulator 驗證。

## 快速總覽

| 晶片 | 說明 | 輸入 | 輸出 |
|------|------|------|------|
| Bit.hdl | 1-bit 暫存器 | in, load | out |
| Register.hdl | 16-bit 暫存器 | in[16], load | out[16] |
| RAM8.hdl | 8 個 16-bit 暫存器組成的記憶體 | in[16], load, address[3] | out[16] |
| RAM64.hdl | 64 個 16-bit 暫存器組成的記憶體 | in[16], load, address[6] | out[16] |
| PC.hdl | 具 load / inc / reset 的 16-bit 計數器 | in[16], load, inc, reset | out[16] |

## 實作順序（相依關係）

```
[ Project 01 Mux ] + [ 內建 DFF ]
              │
              ▼
      1. Bit (1-bit 暫存器)
              │
              ▼
      2. Register (16-bit 暫存器)
              │
              ▼
      3. RAM8 (8 個 Register + 選擇)
              │
              ▼
      4. RAM64 (8 個 RAM8 + 選擇)
              │
              ▼
      5. PC (Register + Inc16 + 優先權控制)
```

**記憶體的遞迴公式**：`RAM(2^k)` = `RAM(2^(k-1))` + 一組選擇器。位址每多 1 bit，容量就翻倍，且只需要把舊的晶片複製一份、外面再包一層 DMux / Mux 即可。本單元全部沿用這個套路。

---

## 逐題解說

### 1. Bit.hdl — 1-bit 暫存器
記憶的最小單位。規格：`load[t] == 1` 時 `out[t+1] = in[t]`，否則 `out` 保持不變。做法是「**先選輸入，再存住**」：
- 用 `Mux` 決定下一個時脈要寫入的值：`load == 0` 時放行目前的 `out`（等於原地不動），`load == 1` 時放行 `in`。
- 再交給內建的 `DFF`（D-type Flip-Flop）暫存，並同時將其輸出接到晶片的 `out`。

這裡的 `Mux` 回饋線（`dffOut` → `Mux`）就是「保持」功能的來源；若拿掉 Mux 直接接 DFF，就變成每個時脈都被覆寫。

```hdl
PARTS:
    Mux(a=dffOut, b=in, sel=load, out=muxOut);
    DFF(in=muxOut, out=dffOut, out=out);
```

### 2. Register.hdl — 16-bit 暫存器
把 16 個 Bit 平行排列，共用同一個 `load` 控制訊號。這裡的位元索引是「低位元在最前」的慣例（`out[0]` 為最小位元），與 Project 01 的 Not16、Add16 保持一致。

```hdl
PARTS:
    Bit(in=in[0],  load=load, out=out[0]);
    Bit(in=in[1],  load=load, out=out[1]);
    // ... 一直到 out[15]
    Bit(in=in[15], load=load, out=out[15]);
```

### 3. RAM8.hdl — 8 個 16-bit 暫存器
`address[3]` 從 8 個暫存器中選一個，分成「寫入」與「讀出」兩條路：
- **寫入路徑**：用 `DMux8Way` 把 `load` 依 `address` 分送，只有被選中的那一路 `load` 為 1，其餘為 0。因此 `in` 會被寫入「指定的位址」。
- **讀出路徑**：用 `Mux8Way16` 依同一個 `address` 從 8 個 Register 中挑出輸出。

由於 Register 內含 DFF，寫入的值要到**下一個時脈**才會從 `out` 出現，這正好符合規格描述。

```hdl
PARTS:
    DMux8Way(in=load, sel=address, a=load0, b=load1, c=load2, d=load3, e=load4, f=load5, g=load6, h=load7);
    Register(in=in, load=load0, out=r0);
    Register(in=in, load=load1, out=r1);
    Register(in=in, load=load2, out=r2);
    Register(in=in, load=load3, out=r3);
    Register(in=in, load=load4, out=r4);
    Register(in=in, load=load5, out=r5);
    Register(in=in, load=load6, out=r6);
    Register(in=in, load=load7, out=r7);
    Mux8Way16(a=r0, b=r1, c=r2, d=r3, e=r4, f=r5, g=r6, h=r7, sel=address, out=out);
```

### 4. RAM64.hdl — 64 個 16-bit 暫存器
沿用 RAM8 的結構，但位址切成兩段使用：
- 高位段 `address[3..5]`（3 bit，8 種組合）負責選擇「哪一個 RAM8」——交給外層的 `DMux8Way` / `Mux8Way16`。
- 低位段 `address[0..2]`（3 bit）負責選擇「該 RAM8 內的第幾個暫存器」——原封不動傳給每個 RAM8。

兩個位址段是**正交的**，因此 6 bit 位址剛好對應 8 × 8 = 64 個位置，容量正好翻 8 倍。

```hdl
PARTS:
    DMux8Way(in=load, sel=address[3..5], a=load0, b=load1, c=load2, d=load3, e=load4, f=load5, g=load6, h=load7);
    RAM8(in=in, load=load0, address=address[0..2], out=r0);
    RAM8(in=in, load=load1, address=address[0..2], out=r1);
    // ... 一直到 r7
    RAM8(in=in, load=load7, address=address[0..2], out=r7);
    Mux8Way16(a=r0, b=r1, c=r2, d=r3, e=r4, f=r5, g=r6, h=r7, sel=address[3..5], out=out);
```

> 這套「DMux 分送 load、Mux 收集 out」的做法一路沿用到 03/b 的 RAM512、RAM4K、RAM16K，每層只多切一段位址出來餵給下一層。

### 5. PC.hdl — 16-bit 程式計數器
PC 是一個「可被控制」的暫存器，四種行為依序有優先權：**reset > load > inc > 維持原值**。做法是在 `Register` 外再串上 `Inc16` 與數個 Mux16，讓每種控制的訊號先經過優先權編碼：

1. `Not(in=reset)` 產生 `notReset`，與 `load`、`inc` 相與，得到「reset 尚未發生的有效訊號」`loadEnabled`、`incEnabled`。
2. `incEnabled` 再與 `notLoad` 相與 → `incActive`（確保 load 優先於 inc）。
3. 資料路徑依序是：目前的 `out` → `Inc16`（得到 out+1）→ 由 `incActive` 選擇「要加一」還是「維持」→ 由 `loadEnabled` 選擇「載入 in」還是前者 → 最後由 `reset` 決定輸出 0 還是上述結果。

```hdl
PARTS:
    // --- 1. 控制訊號優先權編碼：reset > load > inc ---
    Not(in=reset, out=notReset);
    And(a=notReset, b=load, out=loadEnabled);
    And(a=notReset, b=inc,  out=incEnabled);
    Not(in=load,  out=notLoad);
    And(a=incEnabled, b=notLoad, out=incActive);

    // --- 2. 資料路徑：out 或 out+1 ---
    Inc16(in=out, out=incOut);
    Mux16(a=out, b=incOut, sel=incActive, out=incOrHold);

    // --- 3. 載入 in，最後處理 reset ---
    Mux16(a=incOrHold, b=in, sel=loadEnabled, out=loaded);
    Mux16(a=loaded, b=false, sel=reset, out=out);
```

> PC 必須保持「組合邏輯算完 → 交給 Register 暫存」的一輪延遲，所以這裡把 `out` 同時當作 Register 的輸出與整條資料路徑的起點，形成回饋。

---

## 重點設計

- **時序與回饋**：`DFF` 是唯一的記憶來源，所有「保持上一個值」的效果都靠回饋線上的 Mux 完成；資料在 clock edge 才更新。
- **暫存器堆疊**：Bit → Register 是「逐位元平行展開」；Register → RAM8 → RAM64 是「用 DMux 分送寫入、用 Mux 收集讀出」。
- **位址分段**：位址每多一位，記憶體就多一層——高位段選組、低位段往下傳，容量呈 2 的冪次成長。
- **寫入延遲一輪**：寫入的值要到下一個時脈才反映在 `out` 上，這是 RAM8/RAM64 測試腳本檢查的關鍵行為。
- **控制優先權**：PC 以 `Not` / `And` 做出互斥訊號，讓 reset、load、inc 依序排隊，實作 `if / else if` 的硬體語意。
