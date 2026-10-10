// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// // Runs an infinite loop that listens to keyboard input.
(LOOP)
    // 1. 讀取鍵盤輸入
    @KBD
    D=M

    // 若有按鍵 (KBD != 0)，跳至 SET_BLACK；否則設為白色 (0)
    @SET_BLACK
    D;JNE

    @color
    M=0          // 白色
    @DRAW
    0;JMP

(SET_BLACK)
    @color
    M=-1         // 黑色 (全 1)

(DRAW)
    // 2. 初始化指標 addr = SCREEN (16384)
    @SCREEN
    D=A
    @addr
    M=D

(DRAW_LOOP)
    // 3. 檢查是否已經填滿整個螢幕 (當 addr == KBD 時結束)
    @addr
    D=M
    @KBD
    D=D-A
    @LOOP
    D;JEQ        // 若 addr == 24576，跳回最外層繼續監聽鍵盤

    // 4. 將顏色寫入當前螢幕記憶體位址
    @color
    D=M
    @addr
    A=M
    M=D

    // 5. 指標遞增 addr++
    @addr
    M=M+1

    @DRAW_LOOP
    0;JMP