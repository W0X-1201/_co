// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)

// // Multiplies R0 and R1 and stores the result in R2.

    // 1. 初始化 R2 = 0
    @R2
    M=0

    // 2. 設定計數器 i = R1
    @R1
    D=M
    @i
    M=D

(LOOP)
    // 3. 檢查條件：如果 i <= 0，跳出迴圈
    @i
    D=M
    @END
    D;JLE

    // 4. R2 = R2 + R0
    @R0
    D=M
    @R2
    M=M+D

    // 5. 計數器遞減 i = i - 1
    @i
    M=M-1

    @LOOP
    0;JMP

(END)
    // 6. 程式結束：進入無窮迴圈
    @END
    0;JMP