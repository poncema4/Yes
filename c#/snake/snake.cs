// Snake.cs — Cross-platform terminal Snake (Linux, macOS, Windows)
//
// Requirements: .NET 6 or later
//
// How to run:
//   dotnet run

using System;
using System.Collections.Generic;
using System.Threading;

// ─── Constants ────────────────────────────────────────────────────────────────
static class Config
{
    public const int Width     = 40;
    public const int Height    = 20;
    public const int InitSpeed = 150;
    public const int SpeedStep = 10;
    public const int MinSpeed  = 50;
}

// ─── Direction ────────────────────────────────────────────────────────────────
enum Dir { Up, Down, Left, Right }

// ─── Point ────────────────────────────────────────────────────────────────────
readonly record struct Point(int X, int Y)
{
    public Point Move(Dir d) => d switch {
        Dir.Up    => new(X, Y - 1),
        Dir.Down  => new(X, Y + 1),
        Dir.Left  => new(X - 1, Y),
        Dir.Right => new(X + 1, Y),
        _         => this
    };
}

// ─── Terminal helpers ─────────────────────────────────────────────────────────
static class Term
{
    public const int OffX = 1;
    public const int OffY = 2;

    public static void Init()
    {
        Console.OutputEncoding = System.Text.Encoding.UTF8;
        Console.CursorVisible  = false;
        Console.Clear();
    }

    public static void Restore()
    {
        Console.CursorVisible = true;
        Console.ResetColor();
        Console.Clear();
    }

    public static void Write(int x, int y, string s,
        ConsoleColor fg = ConsoleColor.White,
        ConsoleColor bg = ConsoleColor.Black)
    {
        try
        {
            Console.SetCursorPosition(x, y);
            Console.ForegroundColor = fg;
            Console.BackgroundColor = bg;
            Console.Write(s);
            Console.ResetColor();
        }
        catch { /* ignore out-of-bounds writes */ }
    }

    public static void WriteCenter(int y, string s,
        ConsoleColor fg = ConsoleColor.White)
    {
        int x = (Config.Width + 2 - s.Length) / 2 + OffX;
        if (x < 0) x = 0;
        Write(x, y, s, fg);
    }
}

// ─── Board ────────────────────────────────────────────────────────────────────
static class Board
{
    public static int ToScreenX(int bx) => Term.OffX + 1 + bx;
    public static int ToScreenY(int by) => Term.OffY + 1 + by;

    public static void DrawBorder()
    {
        int left  = Term.OffX;
        int top   = Term.OffY;
        int right = Term.OffX + Config.Width  + 1;
        int bot   = Term.OffY + Config.Height + 1;

        for (int x = left + 1; x < right; x++)
        {
            Term.Write(x, top, "-", ConsoleColor.DarkGray);
            Term.Write(x, bot, "-", ConsoleColor.DarkGray);
        }
        for (int y = top + 1; y < bot; y++)
        {
            Term.Write(left,  y, "|", ConsoleColor.DarkGray);
            Term.Write(right, y, "|", ConsoleColor.DarkGray);
        }
        Term.Write(left,  top, "+", ConsoleColor.DarkGray);
        Term.Write(right, top, "+", ConsoleColor.DarkGray);
        Term.Write(left,  bot, "+", ConsoleColor.DarkGray);
        Term.Write(right, bot, "+", ConsoleColor.DarkGray);
    }

    public static void DrawCell(Point p, char ch, ConsoleColor fg)
        => Term.Write(ToScreenX(p.X), ToScreenY(p.Y), ch.ToString(), fg);

    public static void ClearCell(Point p)
        => Term.Write(ToScreenX(p.X), ToScreenY(p.Y), " ");

    public static void DrawScore(int score, int high, int level)
    {
        Term.Write(Term.OffX, 0, new string(' ', Config.Width + 2));
        Term.Write(Term.OffX, 1, new string(' ', Config.Width + 2));
        Term.Write(Term.OffX,      0, "  SNAKE",            ConsoleColor.Green);
        Term.Write(Term.OffX + 9,  0, $"Score: {score}",    ConsoleColor.Cyan);
        Term.Write(Term.OffX + 22, 0, $"Best: {high}",      ConsoleColor.Yellow);
        Term.Write(Term.OffX,      1,
            "  WASD/Arrows: move  P: pause  ESC: quit",
            ConsoleColor.DarkGray);
    }
}

// ─── Food ─────────────────────────────────────────────────────────────────────
static class FoodSpawner
{
    private static readonly Random Rng = new();

    public static Point Spawn(ISet<Point> occupied)
    {
        Point p;
        do {
            p = new Point(Rng.Next(Config.Width), Rng.Next(Config.Height));
        } while (occupied.Contains(p));
        return p;
    }
}

// ─── Snake ────────────────────────────────────────────────────────────────────
class Snake
{
    private readonly LinkedList<Point> _body = new();
    private Dir _dir  = Dir.Right;
    private Dir _next = Dir.Right;

    public IEnumerable<Point> Body => _body;
    public Point Head => _body.First!.Value;

    public Snake(Point start)
    {
        _body.AddFirst(start);
        _body.AddFirst(new Point(start.X + 1, start.Y));
    }

    public void SetDir(Dir d)
    {
        if ((d == Dir.Up    && _dir == Dir.Down)  ||
            (d == Dir.Down  && _dir == Dir.Up)    ||
            (d == Dir.Left  && _dir == Dir.Right) ||
            (d == Dir.Right && _dir == Dir.Left)) return;
        _next = d;
    }

    public (Point newHead, Point? removed) Step(bool grow)
    {
        _dir = _next;
        Point nh = Head.Move(_dir);
        _body.AddFirst(nh);
        if (grow) return (nh, null);
        Point tail = _body.Last!.Value;
        _body.RemoveLast();
        return (nh, tail);
    }

    public bool CollidesWithSelf()
    {
        var h    = Head;
        var node = _body.First!.Next;
        while (node != null)
        {
            if (node.Value == h) return true;
            node = node.Next;
        }
        return false;
    }

    public bool OutOfBounds()
        => Head.X < 0 || Head.X >= Config.Width ||
           Head.Y < 0 || Head.Y >= Config.Height;

    public Point PeekNext() => Head.Move(_next);
}

// ─── Input ────────────────────────────────────────────────────────────────────
static class Input
{
    // Use int instead of Dir? so we can mark it volatile (-1 = no pending input)
    private static volatile int  _pending = -1;
    private static volatile bool _quit    = false;
    private static volatile bool _pause   = false;
    private static volatile bool _space   = false;

    public static Dir? Pending
    {
        get
        {
            int v = _pending;
            if (v < 0) return null;
            _pending = -1;
            return (Dir)v;
        }
    }

    public static bool Quit   => _quit;
    public static bool Paused => _pause;
    public static bool Space  { get { var v = _space; _space = false; return v; } }

    public static void Start()
    {
        var t = new Thread(() =>
        {
            while (true)
            {
                var key = Console.ReadKey(intercept: true);
                switch (key.Key)
                {
                    case ConsoleKey.UpArrow:
                    case ConsoleKey.W:          _pending = (int)Dir.Up;    break;
                    case ConsoleKey.DownArrow:
                    case ConsoleKey.S:          _pending = (int)Dir.Down;  break;
                    case ConsoleKey.LeftArrow:
                    case ConsoleKey.A:          _pending = (int)Dir.Left;  break;
                    case ConsoleKey.RightArrow:
                    case ConsoleKey.D:          _pending = (int)Dir.Right; break;
                    case ConsoleKey.Escape:     _quit    = true;           break;
                    case ConsoleKey.P:          _pause   = !_pause;        break;
                    case ConsoleKey.Spacebar:   _space   = true;           break;
                }
            }
        }) { IsBackground = true, Name = "Input" };
        t.Start();
    }

    public static void Reset()
    {
        _pending = -1;
        _quit    = false;
        _pause   = false;
        _space   = false;
    }
}

// ─── Game ─────────────────────────────────────────────────────────────────────
class Game
{
    private Snake _snake = null!;
    private Point _food;
    private int   _score;
    private int   _high;
    private int   _level;
    private int   _speed;

    public void Run()
    {
        Term.Init();
        Input.Start();

        while (true)
        {
            ShowTitle();
            if (Input.Quit) break;
            Play();
            if (Input.Quit) break;
            ShowGameOver();
            if (Input.Quit) break;
        }

        Term.Restore();
    }

    private void ShowTitle()
    {
        Console.Clear();
        Term.WriteCenter(3,  "  ____  _   _    _    _  __ _____  ", ConsoleColor.Green);
        Term.WriteCenter(4,  " / ___|| \\ | |  / \\  | |/ /| ____| ", ConsoleColor.Green);
        Term.WriteCenter(5,  " \\___ \\|  \\| | / _ \\ | ' / |  _|   ", ConsoleColor.Green);
        Term.WriteCenter(6,  "  ___) | |\\  |/ ___ \\| . \\ | |___  ", ConsoleColor.Green);
        Term.WriteCenter(7,  " |____/|_| \\_/_/   \\_\\_|\\_\\|_____| ", ConsoleColor.Green);
        Term.WriteCenter(10, "Eat @ to grow. Don't hit walls or yourself!", ConsoleColor.White);
        Term.WriteCenter(12, "WASD or Arrow keys to move",                  ConsoleColor.Cyan);
        Term.WriteCenter(13, "P to pause   ESC to quit",                    ConsoleColor.DarkGray);
        Term.WriteCenter(15, "Press SPACE to start...",                     ConsoleColor.Yellow);

        Input.Reset();
        while (!Input.Space && !Input.Quit)
            Thread.Sleep(50);
    }

    private void Play()
    {
        if (Input.Quit) return;

        _score = 0;
        _level = 1;
        _speed = Config.InitSpeed;

        Console.Clear();

        var start  = new Point(Config.Width / 2, Config.Height / 2);
        _snake     = new Snake(start);

        var occupied = new HashSet<Point>(_snake.Body);
        _food = FoodSpawner.Spawn(occupied);

        Board.DrawBorder();
        Board.DrawScore(_score, _high, _level);

        foreach (var p in _snake.Body)
            Board.DrawCell(p, '#', ConsoleColor.Green);

        Board.DrawCell(_food, '@', ConsoleColor.Red);

        Input.Reset();

        while (true)
        {
            if (Input.Quit) return;

            if (Input.Paused)
            {
                Term.WriteCenter(Term.OffY + Config.Height / 2,
                    "  PAUSED - press P to resume  ", ConsoleColor.Yellow);
                while (Input.Paused && !Input.Quit)
                    Thread.Sleep(50);
                Term.WriteCenter(Term.OffY + Config.Height / 2,
                    new string(' ', 34));
            }

            var d = Input.Pending;
            if (d.HasValue) _snake.SetDir(d.Value);

            bool eating = _snake.PeekNext() == _food;

            var (newHead, removed) = _snake.Step(eating);

            if (_snake.OutOfBounds() || _snake.CollidesWithSelf())
                return;

            Board.DrawCell(newHead, '#', ConsoleColor.Green);

            if (removed.HasValue)
                Board.ClearCell(removed.Value);

            if (eating)
            {
                _score++;
                if (_score > _high) _high = _score;

                if (_score % 5 == 0)
                {
                    _level++;
                    _speed = Math.Max(Config.MinSpeed, _speed - Config.SpeedStep * 2);
                }

                var occ = new HashSet<Point>(_snake.Body);
                _food = FoodSpawner.Spawn(occ);
                Board.DrawCell(_food, '@', ConsoleColor.Red);
                Board.DrawScore(_score, _high, _level);
            }

            Thread.Sleep(_speed);
        }
    }

    private void ShowGameOver()
    {
        int cy = Term.OffY + Config.Height / 2 - 3;
        Term.WriteCenter(cy++, "                                  ", ConsoleColor.White);
        Term.WriteCenter(cy++, "  +----------------------------+  ", ConsoleColor.Red);
        Term.WriteCenter(cy++, "  |        GAME  OVER          |  ", ConsoleColor.Red);
        Term.WriteCenter(cy++, $"  |  Score: {_score,-5}  Best: {_high,-5}  |  ", ConsoleColor.White);
        Term.WriteCenter(cy++, "  +----------------------------+  ", ConsoleColor.Red);
        cy++;
        Term.WriteCenter(cy,   "  SPACE: play again   ESC: quit  ", ConsoleColor.DarkGray);

        Input.Reset();
        while (!Input.Space && !Input.Quit)
            Thread.Sleep(50);
    }
}

// ─── Entry point ──────────────────────────────────────────────────────────────
class Program
{
    static void Main() => new Game().Run();
}