// Linux/macOS:  g++ -std=c++17 -O2 -o pong pong.cpp
// Windows MSVC: cl /std:c++17 /O2 pong.cpp
// Windows MinGW: g++ -std=c++17 -O2 -o pong pong.cpp

#include <iostream>
#include <string>
#include <cstdlib>
#include <ctime>
#include <chrono>
#include <thread>

#ifdef _WIN32
  #define PLATFORM_WINDOWS
  #include <windows.h>
  #include <conio.h>
#else
  #define PLATFORM_POSIX
  #include <unistd.h>
  #include <termios.h>
  #include <fcntl.h>
  #include <sys/select.h>
#endif

static const int WIDTH        = 70;
static const int HEIGHT       = 26;
static const int PADDLE_H     = 5;
static const int WIN_SCORE    = 7;
static const int FRAME_MS     = 60;

namespace ansi {
  inline void clearScreen() {
#ifdef PLATFORM_WINDOWS
    HANDLE h = GetStdHandle(STD_OUTPUT_HANDLE);
    COORD origin = {0,0};
    DWORD written;
    CONSOLE_SCREEN_BUFFER_INFO info;
    GetConsoleScreenBufferInfo(h, &info);
    DWORD cells = info.dwSize.X * info.dwSize.Y;
    FillConsoleOutputCharacter(h, ' ', cells, origin, &written);
    FillConsoleOutputAttribute(h, info.wAttributes, cells, origin, &written);
    SetConsoleCursorPosition(h, origin);
#else
    std::cout << "\033[2J\033[H";
    std::cout.flush();
#endif
  }

  inline void gotoxy(int x, int y) {
#ifdef PLATFORM_WINDOWS
    COORD c = { (SHORT)x, (SHORT)y };
    SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), c);
#else
    std::cout << "\033[" << (y+1) << ";" << (x+1) << "H";
#endif
  }

  inline void hideCursor() {
#ifdef PLATFORM_WINDOWS
    CONSOLE_CURSOR_INFO info = {1, FALSE};
    SetConsoleCursorInfo(GetStdHandle(STD_OUTPUT_HANDLE), &info);
#else
    std::cout << "\033[?25l";
    std::cout.flush();
#endif
  }

  inline void showCursor() {
#ifdef PLATFORM_WINDOWS
    CONSOLE_CURSOR_INFO info = {1, TRUE};
    SetConsoleCursorInfo(GetStdHandle(STD_OUTPUT_HANDLE), &info);
#else
    std::cout << "\033[?25h";
    std::cout.flush();
#endif
  }

  inline void setColor(int code) {
#ifdef PLATFORM_WINDOWS
    static const WORD map[] = {7,7,7,7,7,7,7,7,8,7,7,
                                 11, // 11 → cyan
                                 7,
                                 13, // 13 → magenta
                                 14, // 14 → yellow
                                 7};
    WORD attr = (code < (int)(sizeof(map)/sizeof(map[0]))) ? map[code] : 7;
    SetConsoleTextAttribute(GetStdHandle(STD_OUTPUT_HANDLE), attr);
#else
    const char* seq = "\033[0m";
    switch(code) {
      case  8: seq = "\033[90m";  break; // dark gray
      case 11: seq = "\033[96m";  break; // bright cyan
      case 13: seq = "\033[95m";  break; // bright magenta
      case 14: seq = "\033[93m";  break; // bright yellow
      default: seq = "\033[0m";   break;
    }
    std::cout << seq;
#endif
  }

  inline void resetColor() { setColor(0); }
}

#ifdef PLATFORM_POSIX
static termios g_oldTerm;

static void initTerminal() {
  tcgetattr(STDIN_FILENO, &g_oldTerm);
  termios raw = g_oldTerm;
  raw.c_lflag &= ~(ICANON | ECHO);
  raw.c_cc[VMIN]  = 0;
  raw.c_cc[VTIME] = 0;
  tcsetattr(STDIN_FILENO, TCSANOW, &raw);
  int flags = fcntl(STDIN_FILENO, F_GETFL, 0);
  fcntl(STDIN_FILENO, F_SETFL, flags | O_NONBLOCK);
}

static void restoreTerminal() {
  tcsetattr(STDIN_FILENO, TCSANOW, &g_oldTerm);
  int flags = fcntl(STDIN_FILENO, F_GETFL, 0);
  fcntl(STDIN_FILENO, F_SETFL, flags & ~O_NONBLOCK);
}

enum Key { K_NONE=0, K_W, K_S, K_UP, K_DOWN, K_SPACE, K_ESC, K_COUNT };
static bool g_keys[K_COUNT] = {};

static void pollKeys() {
  for (int i = 0; i < K_COUNT; i++) g_keys[i] = false;

  char buf[16];
  int n;
  while ((n = (int)read(STDIN_FILENO, buf, sizeof(buf))) > 0) {
    for (int i = 0; i < n; ) {
      unsigned char c = buf[i];
      if (c == 27 && i+2 < n && buf[i+1] == '[') {
        switch(buf[i+2]) {
          case 'A': g_keys[K_UP]   = true; break;
          case 'B': g_keys[K_DOWN] = true; break;
        }
        i += 3;
      } else {
        switch(c) {
          case 'w': case 'W': g_keys[K_W]     = true; break;
          case 's': case 'S': g_keys[K_S]     = true; break;
          case ' ':           g_keys[K_SPACE]  = true; break;
          case 27:            g_keys[K_ESC]    = true; break;
        }
        i++;
      }
    }
  }
}

static bool keyDown(Key k) { return g_keys[k]; }
#endif 

#ifdef PLATFORM_WINDOWS
enum Key { K_NONE=0, K_W, K_S, K_UP, K_DOWN, K_SPACE, K_ESC, K_COUNT };

static void initTerminal() {
  HANDLE h = GetStdHandle(STD_OUTPUT_HANDLE);
  DWORD mode = 0;
  GetConsoleMode(h, &mode);
  SetConsoleMode(h, mode | ENABLE_VIRTUAL_TERMINAL_PROCESSING);
}
static void restoreTerminal() {}

static void pollKeys() {}

static bool keyDown(Key k) {
  switch(k) {
    case K_W:     return (GetAsyncKeyState('W')       & 0x8000) != 0;
    case K_S:     return (GetAsyncKeyState('S')       & 0x8000) != 0;
    case K_UP:    return (GetAsyncKeyState(VK_UP)     & 0x8000) != 0;
    case K_DOWN:  return (GetAsyncKeyState(VK_DOWN)   & 0x8000) != 0;
    case K_SPACE: return (GetAsyncKeyState(VK_SPACE)  & 0x8000) != 0;
    case K_ESC:   return (GetAsyncKeyState(VK_ESCAPE) & 0x8000) != 0;
    default:      return false;
  }
}
#endif

static void sleepMs(int ms) {
  std::this_thread::sleep_for(std::chrono::milliseconds(ms));
}

static void drawChar(int x, int y, char c, int color = 7) {
  ansi::gotoxy(x, y);
  ansi::setColor(color);
  std::cout << c;
}

static void drawStr(int x, int y, const std::string& s, int color = 7) {
  ansi::gotoxy(x, y);
  ansi::setColor(color);
  std::cout << s;
  ansi::resetColor();
}

static void drawCentered(int y, const std::string& s, int color = 7) {
  int x = (WIDTH - (int)s.size()) / 2;
  if (x < 0) x = 0;
  drawStr(x, y, s, color);
}

struct Ball   { int x, y, dx, dy; };
struct Paddle { int x, y, score;  };

static void drawBorder() {
  ansi::setColor(8);
  for (int x = 0; x < WIDTH; x++) {
    drawChar(x, 0,      '=', 8);
    drawChar(x, HEIGHT, '=', 8);
  }
  for (int y = 1; y < HEIGHT; y++) {
    drawChar(0,       y, '|', 8);
    drawChar(WIDTH-1, y, '|', 8);
  }
  for (int y = 1; y < HEIGHT; y += 2)
    drawChar(WIDTH/2, y, ':', 8);
  ansi::resetColor();
}

static void drawPaddle(const Paddle& p, int color) {
  for (int i = 0; i < PADDLE_H; i++)
    drawChar(p.x, p.y+i, '#', color);
}

static void erasePaddle(const Paddle& p) {
  for (int i = 0; i < PADDLE_H; i++)
    drawChar(p.x, p.y+i, ' ');
}

static void drawBall(const Ball& b)  { drawChar(b.x, b.y, 'O', 14); }
static void eraseBall(const Ball& b) { drawChar(b.x, b.y, ' '); }

static void drawScores(const Paddle& p1, const Paddle& p2) {
  ansi::gotoxy(WIDTH/4, 0);
  ansi::setColor(11);
  std::cout << "P1: " << p1.score << "/" << WIN_SCORE;

  ansi::gotoxy(WIDTH*3/4 - 6, 0);
  ansi::setColor(13);
  std::cout << "P2: " << p2.score << "/" << WIN_SCORE;

  ansi::gotoxy(2, HEIGHT);
  ansi::setColor(8);
  std::cout << " W/S: P1  |  Arrows: P2  |  ESC: Quit ";
  ansi::resetColor();
  std::cout.flush();
}

static void resetBall(Ball& b, int dirX) {
  b.x  = WIDTH/2;
  b.y  = HEIGHT/2;
  b.dx = dirX;
  b.dy = (rand() % 2 == 0) ? 1 : -1;
}

static void showTitle() {
  ansi::clearScreen();
  ansi::setColor(11);
  drawCentered(4,  " ____   ___  _   _  ____  ", 11);
  drawCentered(5,  "|  _ \\ / _ \\| \\ | |/ ___| ", 11);
  drawCentered(6,  "| |_) | | | |  \\| | |  _  ", 11);
  drawCentered(7,  "|  __/| |_| | |\\  | |_| | ", 11);
  drawCentered(8,  "|_|    \\___/|_| \\_|\\____| ", 11);

  drawCentered(11, "First to " + std::to_string(WIN_SCORE) + " wins!", 14);
  drawCentered(13, "P1  >>>  W / S keys",        11);
  drawCentered(14, "P2  >>>  UP / DOWN arrows",  13);
  drawCentered(17, "Press SPACE to start...",     7);
  ansi::resetColor();
  std::cout.flush();

  while (true) {
    pollKeys();
    if (keyDown(K_SPACE)) break;
    if (keyDown(K_ESC))   { ansi::showCursor(); restoreTerminal(); exit(0); }
    sleepMs(50);
  }
  sleepMs(200);
}

static void showGameOver(const Paddle& p1, const Paddle& p2) {
  ansi::clearScreen();
  bool p1won    = (p1.score >= WIN_SCORE);
  int  winColor = p1won ? 11 : 13;
  std::string winner = p1won ? "PLAYER 1 WINS!" : "PLAYER 2 WINS!";

  drawCentered(5,  "+------------------------+", winColor);
  drawCentered(6,  "|                        |", winColor);
  drawCentered(7,  "|     " + winner + "     |", winColor);
  drawCentered(8,  "|                        |", winColor);
  drawCentered(9,  "+------------------------+", winColor);

  std::string sc = "Final Score:  P1 " + std::to_string(p1.score)
                 + "  -  " + std::to_string(p2.score) + "  P2";
  drawCentered(12, sc, 7);
  drawCentered(15, "Play again? (SPACE)   Quit? (ESC)", 8);
  ansi::resetColor();
  std::cout.flush();

  while (true) {
    pollKeys();
    if (keyDown(K_SPACE)) { sleepMs(200); return; }
    if (keyDown(K_ESC))   { ansi::showCursor(); restoreTerminal(); exit(0); }
    sleepMs(50);
  }
}

static void playGame() {
  ansi::clearScreen();
  ansi::hideCursor();

  Ball   ball = { WIDTH/2, HEIGHT/2, 1, 1 };
  Paddle p1   = { 2,         HEIGHT/2 - PADDLE_H/2, 0 };
  Paddle p2   = { WIDTH - 3, HEIGHT/2 - PADDLE_H/2, 0 };

  drawBorder();
  drawScores(p1, p2);

  while (true) {
    pollKeys();

    if (keyDown(K_ESC)) { ansi::showCursor(); restoreTerminal(); exit(0); }

    erasePaddle(p1);
    erasePaddle(p2);
    eraseBall(ball);

    if (keyDown(K_W)    && p1.y > 1)                p1.y--;
    if (keyDown(K_S)    && p1.y < HEIGHT - PADDLE_H) p1.y++;
    if (keyDown(K_UP)   && p2.y > 1)                p2.y--;
    if (keyDown(K_DOWN) && p2.y < HEIGHT - PADDLE_H) p2.y++;

    ball.x += ball.dx;
    ball.y += ball.dy;

    if (ball.y <= 1 || ball.y >= HEIGHT-1) ball.dy *= -1;

    if (ball.x == p1.x+1 && ball.y >= p1.y && ball.y < p1.y+PADDLE_H)
      ball.dx *= -1;
    if (ball.x == p2.x-1 && ball.y >= p2.y && ball.y < p2.y+PADDLE_H)
      ball.dx *= -1;

    if (ball.x <= 1) {
      p2.score++;
      if (p2.score >= WIN_SCORE) { showGameOver(p1, p2); return; }
      resetBall(ball, 1);
      drawBorder(); drawScores(p1, p2);
      sleepMs(600);
    }
    if (ball.x >= WIDTH-2) {
      p1.score++;
      if (p1.score >= WIN_SCORE) { showGameOver(p1, p2); return; }
      resetBall(ball, -1);
      drawBorder(); drawScores(p1, p2);
      sleepMs(600);
    }

    drawBorder();
    drawScores(p1, p2);
    drawPaddle(p1, 11);
    drawPaddle(p2, 13);
    drawBall(ball);
    std::cout.flush();

    sleepMs(FRAME_MS);
  }
}

int main() {
  srand((unsigned)time(nullptr));
  initTerminal();
  while (true) {
    showTitle();
    playGame();
  }
}