#include <windows.h>
#include <iostream>
#include <string>
#include <sstream>

#define PADDLE_HEIGHT 5
#define BALL_SPEED 60
#define WIDTH 70
#define HEIGHT 26
#define WIN_SCORE 7

struct Ball   { int x, y, dx, dy; };
struct Paddle { int x, y, score; };

HANDLE hConsole = GetStdHandle(STD_OUTPUT_HANDLE);

void setColor(int fg, int bg = 0) {
    SetConsoleTextAttribute(hConsole, (bg << 4) | fg);
}

void gotoxy(int x, int y) {
    COORD c = { (SHORT)x, (SHORT)y };
    SetConsoleCursorPosition(hConsole, c);
}

void hideCursor() {
    CONSOLE_CURSOR_INFO info = { 1, FALSE };
    SetConsoleCursorInfo(hConsole, &info);
}

void draw(int x, int y, char ch, int color = 7) {
    gotoxy(x, y);
    setColor(color);
    std::cout << ch;
}

void drawStr(int x, int y, const std::string& s, int color = 7) {
    gotoxy(x, y);
    setColor(color);
    std::cout << s;
}

void drawBorder() {
    setColor(8);
    for (int x = 0; x < WIDTH; x++) {
        draw(x, 0,      '=', 8);
        draw(x, HEIGHT, '=', 8);
    }
    for (int y = 1; y < HEIGHT; y++) {
        draw(0,       y, '|', 8);
        draw(WIDTH-1, y, '|', 8);
    }
    for (int y = 1; y < HEIGHT; y += 2)
        draw(WIDTH / 2, y, ':', 8);
}

void drawPaddle(const Paddle& p, int color) {
    for (int i = 0; i < PADDLE_HEIGHT; i++)
        draw(p.x, p.y + i, '#', color);
}

void erasePaddle(const Paddle& p) {
    for (int i = 0; i < PADDLE_HEIGHT; i++)
        draw(p.x, p.y + i, ' ');
}

void drawBall(const Ball& b) {
    draw(b.x, b.y, 'O', 14);
}

void eraseBall(const Ball& b) {
    draw(b.x, b.y, ' ');
}

void drawScores(const Paddle& p1, const Paddle& p2) {
    // P1 score (left)
    gotoxy(WIDTH / 4, 0);
    setColor(11); // cyan
    std::cout << "P1: " << p1.score << "/" << WIN_SCORE;

    // P2 score (right)
    gotoxy(WIDTH * 3 / 4 - 6, 0);
    setColor(13); // magenta
    std::cout << "P2: " << p2.score << "/" << WIN_SCORE;

    // Controls hint
    gotoxy(2, HEIGHT);
    setColor(8);
    std::cout << " W/S: P1  |  Arrows: P2  |  ESC: Quit ";
}

void drawCenteredStr(int y, const std::string& s, int color) {
    int x = (WIDTH - (int)s.size()) / 2;
    drawStr(x, y, s, color);
}

void showTitleScreen() {
    system("cls");
    setColor(11);
    drawCenteredStr(4,  R"( ____   ___  _   _  ____  )", 11);
    drawCenteredStr(5,  R"(|  _ \ / _ \| \ | |/ ___| )", 11);
    drawCenteredStr(6,  R"(| |_) | | | |  \| | |  _  )", 11);
    drawCenteredStr(7,  R"(|  __/| |_| | |\  | |_| | )", 11);
    drawCenteredStr(8,  R"(|_|    \___/|_| \_|\____| )", 11);

    drawCenteredStr(11, "First to " + std::to_string(WIN_SCORE) + " wins!", 14);
    drawCenteredStr(13, "P1  >>>  W / S keys", 11);
    drawCenteredStr(14, "P2  >>>  UP / DOWN arrows", 13);
    drawCenteredStr(17, "Press SPACE to start...", 7);
    setColor(7);

    while (!(GetAsyncKeyState(VK_SPACE) & 0x8000))
        Sleep(50);
    Sleep(200);
}

void showGameOver(const Paddle& p1, const Paddle& p2) {
    system("cls");
    bool p1won = p1.score >= WIN_SCORE;
    int winColor = p1won ? 11 : 13;
    std::string winner = p1won ? "PLAYER 1 WINS!" : "PLAYER 2 WINS!";

    drawCenteredStr(5,  "+------------------------+", winColor);
    drawCenteredStr(6,  "|                        |", winColor);
    drawCenteredStr(7,  "|     " + winner + "     |", winColor);
    drawCenteredStr(8,  "|                        |", winColor);
    drawCenteredStr(9,  "+------------------------+", winColor);

    std::string scoreStr = "Final Score:  P1 " + std::to_string(p1.score) +
                           "  -  " + std::to_string(p2.score) + "  P2";
    drawCenteredStr(12, scoreStr, 7);
    drawCenteredStr(15, "Play again? (SPACE)   Quit? (ESC)", 8);
    setColor(7);

    while (true) {
        if (GetAsyncKeyState(VK_SPACE) & 0x8000) { Sleep(200); return; }
        if (GetAsyncKeyState(VK_ESCAPE) & 0x8000) { exit(0); }
        Sleep(50);
    }
}

void resetBall(Ball& ball, int dirX) {
    ball.x  = WIDTH / 2;
    ball.y  = HEIGHT / 2;
    ball.dx = dirX;
    ball.dy = (rand() % 2 == 0) ? 1 : -1;
}

void playGame() {
    system("cls");
    hideCursor();

    Ball   ball = { WIDTH/2, HEIGHT/2, 1, 1 };
    Paddle p1   = { 2,         HEIGHT/2 - PADDLE_HEIGHT/2, 0 };
    Paddle p2   = { WIDTH - 3, HEIGHT/2 - PADDLE_HEIGHT/2, 0 };

    drawBorder();
    drawScores(p1, p2);

    while (true) {
        if (GetAsyncKeyState(VK_ESCAPE) & 0x8000) exit(0);

        erasePaddle(p1);
        erasePaddle(p2);
        eraseBall(ball);

        // Player 1: W / S
        if (GetAsyncKeyState('W') & 0x8000 && p1.y > 1)
            p1.y--;
        if (GetAsyncKeyState('S') & 0x8000 && p1.y < HEIGHT - PADDLE_HEIGHT)
            p1.y++;

        // Player 2: arrows
        if (GetAsyncKeyState(VK_UP)   & 0x8000 && p2.y > 1)
            p2.y--;
        if (GetAsyncKeyState(VK_DOWN) & 0x8000 && p2.y < HEIGHT - PADDLE_HEIGHT)
            p2.y++;

        // Move ball
        ball.x += ball.dx;
        ball.y += ball.dy;

        // Bounce top/bottom
        if (ball.y <= 1 || ball.y >= HEIGHT - 1) ball.dy *= -1;

        // Bounce off paddles
        if (ball.x == p1.x + 1 && ball.y >= p1.y && ball.y < p1.y + PADDLE_HEIGHT)
            ball.dx *= -1;
        if (ball.x == p2.x - 1 && ball.y >= p2.y && ball.y < p2.y + PADDLE_HEIGHT)
            ball.dx *= -1;

        // Scoring
        if (ball.x <= 1) {
            p2.score++;
            if (p2.score >= WIN_SCORE) { showGameOver(p1, p2); return; }
            resetBall(ball, 1);
            drawBorder();
            drawScores(p1, p2);
            Sleep(600);
        }
        if (ball.x >= WIDTH - 2) {
            p1.score++;
            if (p1.score >= WIN_SCORE) { showGameOver(p1, p2); return; }
            resetBall(ball, -1);
            drawBorder();
            drawScores(p1, p2);
            Sleep(600);
        }

        drawBorder();
        drawScores(p1, p2);
        drawPaddle(p1, 11); // cyan
        drawPaddle(p2, 13); // magenta
        drawBall(ball);

        Sleep(BALL_SPEED);
    }
}

int main() {
    srand((unsigned)GetTickCount());
    while (true) {
        showTitleScreen();
        playGame();
    }
}