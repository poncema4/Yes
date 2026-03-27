import java.util.*;

public class connect_four {

    static final int ROWS = 6;
    static final int COLS = 7;
    static final char EMPTY = '.';
    static final char PLAYER_1 = '●';
    static final char PLAYER_2 = '○';

    static final String RESET = "\033[0m";
    static final String BOLD = "\033[1m";
    static final String RED = "\033[91m";
    static final String YELLOW = "\033[93m";
    static final String BLUE = "\033[94m";
    static final String CYAN = "\033[96m";
    static final String GREEN = "\033[92m";
    static final String MAGENTA = "\033[95m";
    static final String WHITE = "\033[97m";
    static final String DIM = "\033[2m";
    static final String BG_BLUE = "\033[44m";
    static final String BG_RED = "\033[41m";
    static final String BG_YELLOW = "\033[43m";
    static final String BG_GREEN = "\033[42m";
    static final String BLINK = "\033[5m";

    static char[][] board = new char[ROWS][COLS];
    static boolean[][] winHighlight = new boolean[ROWS][COLS];
    static String player1Name;
    static String player2Name;
    static boolean vsAI = false;
    static int aiDifficulty = 3;
    static int player1Wins = 0;
    static int player2Wins = 0;
    static int draws = 0;
    static int gamesPlayed = 0;
    static Scanner scanner = new Scanner(System.in);
    static Random random = new Random();
    static int lastMoveRow = -1;
    static int lastMoveCol = -1;

    public static void main(String[] args) {
        clearScreen();
        printTitle();
        setupGame();

        boolean playAgain = true;
        while (playAgain) {
            initBoard();
            playGame();
            gamesPlayed++;
            playAgain = askPlayAgain();
        }

        printFinalStats();
        System.out.println(CYAN + "\n  Thanks for playing Connect Four! Goodbye! 👋\n" + RESET);
    }

    static void printTitle() {
        System.out.println();
        System.out.println(RED + "   ██████╗ ██████╗ ███╗   ██╗███╗   ██╗███████╗ ██████╗████████╗" + RESET);
        System.out.println(YELLOW + "  ██╔════╝██╔═══██╗████╗  ██║████╗  ██║██╔════╝██╔════╝╚══██╔══╝" + RESET);
        System.out.println(RED + "  ██║     ██║   ██║██╔██╗ ██║██╔██╗ ██║█████╗  ██║        ██║   " + RESET);
        System.out.println(YELLOW + "  ██║     ██║   ██║██║╚██╗██║██║╚██╗██║██╔══╝  ██║        ██║   " + RESET);
        System.out.println(RED + "  ╚██████╗╚██████╔╝██║ ╚████║██║ ╚████║███████╗╚██████╗   ██║   " + RESET);
        System.out.println(YELLOW + "   ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝ ╚═════╝   ╚═╝   " + RESET);
        System.out.println();
        System.out.println(BOLD + RED + "              ███████╗ ██████╗ ██╗   ██╗██████╗ " + RESET);
        System.out.println(BOLD + YELLOW + "              ██╔════╝██╔═══██╗██║   ██║██╔══██╗" + RESET);
        System.out.println(BOLD + RED + "              █████╗  ██║   ██║██║   ██║██████╔╝" + RESET);
        System.out.println(BOLD + YELLOW + "              ██╔══╝  ██║   ██║██║   ██║██╔══██╗" + RESET);
        System.out.println(BOLD + RED + "              ██║     ╚██████╔╝╚██████╔╝██║  ██║" + RESET);
        System.out.println(BOLD + YELLOW + "              ╚═╝      ╚═════╝  ╚═════╝ ╚═╝  ╚═╝" + RESET);
        System.out.println();
        System.out.println(DIM + WHITE + "           ─── The Classic Strategy Game ───" + RESET);
        System.out.println();
    }

    static void setupGame() {
        System.out.println(BOLD + CYAN + "  ┌─────────────────────────────────┐" + RESET);
        System.out.println(BOLD + CYAN + "  │         GAME MODE SELECT        │" + RESET);
        System.out.println(BOLD + CYAN + "  ├─────────────────────────────────┤" + RESET);
        System.out.println(CYAN + "  │  " + WHITE + "1." + CYAN + " Player vs Player            │" + RESET);
        System.out.println(CYAN + "  │  " + WHITE + "2." + CYAN + " Player vs Computer           │" + RESET);
        System.out.println(BOLD + CYAN + "  └─────────────────────────────────┘" + RESET);
        System.out.print(WHITE + "\n  Choose mode (1-2): " + RESET);

        int mode = getIntInput(1, 2);
        vsAI = (mode == 2);

        System.out.print(WHITE + "\n  Player 1 name: " + RESET);
        player1Name = scanner.nextLine().trim();
        if (player1Name.isEmpty()) player1Name = "Player 1";

        if (vsAI) {
            player2Name = "CPU";
            System.out.println();
            System.out.println(BOLD + CYAN + "  ┌─────────────────────────────────┐" + RESET);
            System.out.println(BOLD + CYAN + "  │        DIFFICULTY SELECT         │" + RESET);
            System.out.println(BOLD + CYAN + "  ├─────────────────────────────────┤" + RESET);
            System.out.println(CYAN + "  │  " + GREEN + "1." + CYAN + " Easy    " + DIM + "- Random moves" + RESET + CYAN + "       │" + RESET);
            System.out.println(CYAN + "  │  " + YELLOW + "2." + CYAN + " Medium  " + DIM + "- Some strategy" + RESET + CYAN + "    │" + RESET);
            System.out.println(CYAN + "  │  " + RED + "3." + CYAN + " Hard    " + DIM + "- Minimax AI" + RESET + CYAN + "       │" + RESET);
            System.out.println(BOLD + CYAN + "  └─────────────────────────────────┘" + RESET);
            System.out.print(WHITE + "\n  Choose difficulty (1-3): " + RESET);
            aiDifficulty = getIntInput(1, 3);
        } else {
            System.out.print(WHITE + "  Player 2 name: " + RESET);
            player2Name = scanner.nextLine().trim();
            if (player2Name.isEmpty()) player2Name = "Player 2";
        }
    }

    static void initBoard() {
        for (int r = 0; r < ROWS; r++) {
            Arrays.fill(board[r], EMPTY);
            Arrays.fill(winHighlight[r], false);
        }
        lastMoveRow = -1;
        lastMoveCol = -1;
    }

    static void playGame() {
        char currentPiece = PLAYER_1;
        String currentName = player1Name;
        boolean gameOver = false;

        while (!gameOver) {
            clearScreen();
            printScoreboard();
            printBoard();

            int col;
            if (vsAI && currentPiece == PLAYER_2) {
                System.out.println(MAGENTA + "\n  🤖 " + player2Name + " is thinking..." + RESET);
                sleep(500 + random.nextInt(500));
                col = getAIMove(currentPiece);
            } else {
                System.out.println();
                String color = (currentPiece == PLAYER_1) ? RED : YELLOW;
                System.out.print(color + "  " + currentName + "'s turn" + RESET);
                System.out.print(WHITE + " — drop in column (1-7): " + RESET);
                col = getColumnInput();
                if (col == -1) { // quit
                    System.out.println(CYAN + "\n  Game abandoned." + RESET);
                    return;
                }
            }

            int row = dropPiece(col, currentPiece);
            if (row == -1) {
                continue;
            }

            lastMoveRow = row;
            lastMoveCol = col;

            if (checkWin(row, col, currentPiece)) {
                clearScreen();
                printScoreboard();
                printBoard();
                printWinMessage(currentName, currentPiece);
                if (currentPiece == PLAYER_1) player1Wins++;
                else player2Wins++;
                gameOver = true;
            } else if (isBoardFull()) {
                clearScreen();
                printScoreboard();
                printBoard();
                printDrawMessage();
                draws++;
                gameOver = true;
            } else {
                if (currentPiece == PLAYER_1) {
                    currentPiece = PLAYER_2;
                    currentName = player2Name;
                } else {
                    currentPiece = PLAYER_1;
                    currentName = player1Name;
                }
            }
        }
    }

    static void printScoreboard() {
        System.out.println();
        System.out.println(BOLD + WHITE + "  ╔═══════════════════════════════════════════════╗" + RESET);
        String p1Display = String.format("  ║  " + RED + BOLD + "%-14s %s %2d" + RESET + WHITE,
                player1Name, "●", player1Wins);
        String middle = DIM + "  │  " + RESET + WHITE;
        String p2Display = String.format(YELLOW + BOLD + "%-14s %s %2d" + RESET + WHITE + "  ║",
                player2Name, "○", player2Wins);
        System.out.println(p1Display + middle + p2Display + RESET);
        String drawLine = String.format("  ║  " + DIM + "Draws: %-3d" + RESET + WHITE
                + "                 " + DIM + "Games: %-3d" + RESET + WHITE + "       ║", draws, gamesPlayed);
        System.out.println(drawLine + RESET);
        System.out.println(BOLD + WHITE + "  ╚═══════════════════════════════════════════════╝" + RESET);
        System.out.println();
    }

    static void printBoard() {
         Column numbers
        System.out.print("     ");
        for (int c = 0; c < COLS; c++) {
            if (c == lastMoveCol) {
                System.out.print(BOLD + GREEN + " " + (c + 1) + "  " + RESET);
            } else {
                System.out.print(DIM + WHITE + " " + (c + 1) + "  " + RESET);
            }
        }
        System.out.println();

        System.out.println(BLUE + "    ╔════╤════╤════╤════╤════╤════╤════╗" + RESET);

        for (int r = 0; r < ROWS; r++) {
            System.out.print(BLUE + "    ║" + RESET);
            for (int c = 0; c < COLS; c++) {
                char piece = board[r][c];
                if (winHighlight[r][c]) {
                    if (piece == PLAYER_1) {
                        System.out.print(BG_GREEN + BOLD + RED + " " + piece + " " + RESET);
                    } else {
                        System.out.print(BG_GREEN + BOLD + YELLOW + " " + piece + " " + RESET);
                    }
                } else if (r == lastMoveRow && c == lastMoveCol) {
                    if (piece == PLAYER_1) {
                        System.out.print(BOLD + RED + " " + piece + " " + RESET);
                    } else {
                        System.out.print(BOLD + YELLOW + " " + piece + " " + RESET);
                    }
                } else if (piece == PLAYER_1) {
                    System.out.print(RED + " " + piece + " " + RESET);
                } else if (piece == PLAYER_2) {
                    System.out.print(YELLOW + " " + piece + " " + RESET);
                } else {
                    System.out.print(DIM + " · " + RESET);
                }
                if (c < COLS - 1) {
                    System.out.print(BLUE + "│" + RESET);
                }
            }
            System.out.println(BLUE + "║" + RESET);
            if (r < ROWS - 1) {
                System.out.println(BLUE + "    ╟────┼────┼────┼────┼────┼────┼────╢" + RESET);
            }
        }
        System.out.println(BLUE + "    ╚════╧════╧════╧════╧════╧════╧════╝" + RESET);
    }

    static void printWinMessage(String name, char piece) {
        String color = (piece == PLAYER_1) ? RED : YELLOW;
        System.out.println();
        System.out.println(color + BOLD + "  ╔═══════════════════════════════════════╗" + RESET);
        System.out.println(color + BOLD + "  ║                                       ║" + RESET);
        String msg = String.format("  ║   🎉  %s WINS!  🎉", name);
        System.out.print(color + BOLD + msg);
        int pad = 42 - msg.length() + 4;
        for (int i = 0; i < pad; i++) System.out.print(" ");
        System.out.println("║" + RESET);
        System.out.println(color + BOLD + "  ║                                       ║" + RESET);
        System.out.println(color + BOLD + "  ╚═══════════════════════════════════════╝" + RESET);
    }

    static void printDrawMessage() {
        System.out.println();
        System.out.println(CYAN + BOLD + "  ╔═══════════════════════════════════════╗" + RESET);
        System.out.println(CYAN + BOLD + "  ║                                       ║" + RESET);
        System.out.println(CYAN + BOLD + "  ║        🤝  It's a DRAW!  🤝           ║" + RESET);
        System.out.println(CYAN + BOLD + "  ║                                       ║" + RESET);
        System.out.println(CYAN + BOLD + "  ╚═══════════════════════════════════════╝" + RESET);
    }

    static void printFinalStats() {
        System.out.println();
        System.out.println(BOLD + CYAN + "  ╔═══════════════════════════════════════╗" + RESET);
        System.out.println(BOLD + CYAN + "  ║          FINAL STATISTICS             ║" + RESET);
        System.out.println(BOLD + CYAN + "  ╠═══════════════════════════════════════╣" + RESET);
        System.out.printf(CYAN + "  ║  Games Played:  %-21d║%n" + RESET, gamesPlayed);
        System.out.printf(RED + "  ║  %-14s wins: %-16d" + CYAN + "║%n" + RESET, player1Name, player1Wins);
        System.out.printf(YELLOW + "  ║  %-14s wins: %-16d" + CYAN + "║%n" + RESET, player2Name, player2Wins);
        System.out.printf(CYAN + "  ║  Draws:         %-21d║%n" + RESET, draws);
        System.out.println(BOLD + CYAN + "  ╚═══════════════════════════════════════╝" + RESET);
    }

    static int dropPiece(int col, char piece) {
        for (int r = ROWS - 1; r >= 0; r--) {
            if (board[r][col] == EMPTY) {
                board[r][col] = piece;
                return r;
            }
        }
        return -1;
    }

    static void undoPiece(int col) {
        for (int r = 0; r < ROWS; r++) {
            if (board[r][col] != EMPTY) {
                board[r][col] = EMPTY;
                return;
            }
        }
    }

    static boolean isColumnFull(int col) {
        return board[0][col] != EMPTY;
    }

    static boolean isBoardFull() {
        for (int c = 0; c < COLS; c++) {
            if (!isColumnFull(c)) return false;
        }
        return true;
    }

    static boolean checkWin(int row, int col, char piece) {
        int[][] directions = {{0, 1}, {1, 0}, {1, 1}, {1, -1}};

        for (int[] dir : directions) {
            List<int[]> cells = new ArrayList<>();
            cells.add(new int[]{row, col});

            for (int i = 1; i < 4; i++) {
                int r = row + dir[0] * i;
                int c = col + dir[1] * i;
                if (r >= 0 && r < ROWS && c >= 0 && c < COLS && board[r][c] == piece) {
                    cells.add(new int[]{r, c});
                } else break;
            }
            for (int i = 1; i < 4; i++) {
                int r = row - dir[0] * i;
                int c = col - dir[1] * i;
                if (r >= 0 && r < ROWS && c >= 0 && c < COLS && board[r][c] == piece) {
                    cells.add(new int[]{r, c});
                } else break;
            }

            if (cells.size() >= 4) {
                for (int[] cell : cells) {
                    winHighlight[cell[0]][cell[1]] = true;
                }
                return true;
            }
        }
        return false;
    }

    static boolean checkWinSimple(int row, int col, char piece) {
        int[][] directions = {{0, 1}, {1, 0}, {1, 1}, {1, -1}};
        for (int[] dir : directions) {
            int count = 1;
            for (int i = 1; i < 4; i++) {
                int r = row + dir[0] * i;
                int c = col + dir[1] * i;
                if (r >= 0 && r < ROWS && c >= 0 && c < COLS && board[r][c] == piece) count++;
                else break;
            }
            for (int i = 1; i < 4; i++) {
                int r = row - dir[0] * i;
                int c = col - dir[1] * i;
                if (r >= 0 && r < ROWS && c >= 0 && c < COLS && board[r][c] == piece) count++;
                else break;
            }
            if (count >= 4) return true;
        }
        return false;
    }

    static int getAIMove(char aiPiece) {
        switch (aiDifficulty) {
            case 1: return getEasyMove();
            case 2: return getMediumMove(aiPiece);
            case 3: return getHardMove(aiPiece);
            default: return getHardMove(aiPiece);
        }
    }

    static int getEasyMove() {
        List<Integer> valid = getValidColumns();
        return valid.get(random.nextInt(valid.size()));
    }

    static int getMediumMove(char aiPiece) {
        char humanPiece = (aiPiece == PLAYER_1) ? PLAYER_2 : PLAYER_1;

        for (int c : getValidColumns()) {
            int r = dropPiece(c, aiPiece);
            if (checkWinSimple(r, c, aiPiece)) { undoPiece(c); return c; }
            undoPiece(c);
        }
        for (int c : getValidColumns()) {
            int r = dropPiece(c, humanPiece);
            if (checkWinSimple(r, c, humanPiece)) { undoPiece(c); return c; }
            undoPiece(c);
        }
        if (!isColumnFull(3)) return 3;
        return getEasyMove();
    }

    static int getHardMove(char aiPiece) {
        int bestScore = Integer.MIN_VALUE;
        int bestCol = 3;
        List<Integer> validCols = getValidColumns();

        Collections.shuffle(validCols);

        validCols.sort(Comparator.comparingInt(c -> Math.abs(c - 3)));

        int depth = 7;

        for (int col : validCols) {
            int row = dropPiece(col, aiPiece);
            int score = minimax(depth - 1, Integer.MIN_VALUE, Integer.MAX_VALUE, false, aiPiece);
            undoPiece(col);
            if (score > bestScore) {
                bestScore = score;
                bestCol = col;
            }
        }
        return bestCol;
    }

    static int minimax(int depth, int alpha, int beta, boolean maximizing, char aiPiece) {
        char humanPiece = (aiPiece == PLAYER_1) ? PLAYER_2 : PLAYER_1;

        if (hasAnyWin(aiPiece)) return 100000 + depth;
        if (hasAnyWin(humanPiece)) return -100000 - depth;
        if (isBoardFull() || depth == 0) return evaluateBoard(aiPiece);

        List<Integer> validCols = getValidColumns();
        validCols.sort(Comparator.comparingInt(c -> Math.abs(c - 3)));

        if (maximizing) {
            int maxEval = Integer.MIN_VALUE;
            for (int col : validCols) {
                int row = dropPiece(col, aiPiece);
                int eval = minimax(depth - 1, alpha, beta, false, aiPiece);
                undoPiece(col);
                maxEval = Math.max(maxEval, eval);
                alpha = Math.max(alpha, eval);
                if (beta <= alpha) break;
            }
            return maxEval;
        } else {
            int minEval = Integer.MAX_VALUE;
            for (int col : validCols) {
                int row = dropPiece(col, humanPiece);
                int eval = minimax(depth - 1, alpha, beta, true, aiPiece);
                undoPiece(col);
                minEval = Math.min(minEval, eval);
                beta = Math.min(beta, eval);
                if (beta <= alpha) break;
            }
            return minEval;
        }
    }

    static boolean hasAnyWin(char piece) {
        for (int r = 0; r < ROWS; r++) {
            for (int c = 0; c < COLS; c++) {
                if (board[r][c] == piece && checkWinSimple(r, c, piece)) return true;
            }
        }
        return false;
    }

    static int evaluateBoard(char aiPiece) {
        char humanPiece = (aiPiece == PLAYER_1) ? PLAYER_2 : PLAYER_1;
        int score = 0;

        for (int r = 0; r < ROWS; r++) {
            if (board[r][3] == aiPiece) score += 3;
            if (board[r][3] == humanPiece) score -= 3;
        }

        for (int r = 0; r < ROWS; r++) {
            for (int c = 0; c <= COLS - 4; c++) {
                score += evaluateWindow(r, c, 0, 1, aiPiece, humanPiece);
            }
        }
        for (int r = 0; r <= ROWS - 4; r++) {
            for (int c = 0; c < COLS; c++) {
                score += evaluateWindow(r, c, 1, 0, aiPiece, humanPiece);
            }
        }
        for (int r = 0; r <= ROWS - 4; r++) {
            for (int c = 0; c <= COLS - 4; c++) {
                score += evaluateWindow(r, c, 1, 1, aiPiece, humanPiece);
            }
        }
        for (int r = 0; r <= ROWS - 4; r++) {
            for (int c = 3; c < COLS; c++) {
                score += evaluateWindow(r, c, 1, -1, aiPiece, humanPiece);
            }
        }

        return score;
    }

    static int evaluateWindow(int startR, int startC, int dr, int dc, char aiPiece, char humanPiece) {
        int aiCount = 0, humanCount = 0, emptyCount = 0;
        for (int i = 0; i < 4; i++) {
            char cell = board[startR + dr * i][startC + dc * i];
            if (cell == aiPiece) aiCount++;
            else if (cell == humanPiece) humanCount++;
            else emptyCount++;
        }

        if (aiCount == 4) return 10000;
        if (humanCount == 4) return -10000;
        if (aiCount == 3 && emptyCount == 1) return 50;
        if (humanCount == 3 && emptyCount == 1) return -80;
        if (aiCount == 2 && emptyCount == 2) return 10;
        if (humanCount == 2 && emptyCount == 2) return -10;
        return 0;
    }

    static List<Integer> getValidColumns() {
        List<Integer> valid = new ArrayList<>();
        for (int c = 0; c < COLS; c++) {
            if (!isColumnFull(c)) valid.add(c);
        }
        return valid;
    }

    static int getColumnInput() {
        while (true) {
            String input = scanner.nextLine().trim().toLowerCase();
            if (input.equals("q") || input.equals("quit") || input.equals("exit")) {
                return -1;
            }
            try {
                int col = Integer.parseInt(input) - 1;
                if (col >= 0 && col < COLS && !isColumnFull(col)) {
                    return col;
                } else if (col >= 0 && col < COLS) {
                    System.out.print(RED + "  Column is full! Choose another (1-7): " + RESET);
                } else {
                    System.out.print(RED + "  Invalid! Enter 1-7 (or 'q' to quit): " + RESET);
                }
            } catch (NumberFormatException e) {
                System.out.print(RED + "  Invalid! Enter 1-7 (or 'q' to quit): " + RESET);
            }
        }
    }

    static int getIntInput(int min, int max) {
        while (true) {
            try {
                int val = Integer.parseInt(scanner.nextLine().trim());
                if (val >= min && val <= max) return val;
                System.out.print(RED + "  Enter " + min + "-" + max + ": " + RESET);
            } catch (NumberFormatException e) {
                System.out.print(RED + "  Enter " + min + "-" + max + ": " + RESET);
            }
        }
    }

    static boolean askPlayAgain() {
        System.out.print(WHITE + "\n  Play again? (y/n): " + RESET);
        while (true) {
            String input = scanner.nextLine().trim().toLowerCase();
            if (input.startsWith("y")) return true;
            if (input.startsWith("n")) return false;
            System.out.print(RED + "  Enter y or n: " + RESET);
        }
    }

    static void clearScreen() {
        System.out.print("\033[H\033[2J");
        System.out.flush();
    }

    static void sleep(int ms) {
        try { Thread.sleep(ms); } catch (InterruptedException ignored) {}
    }
}
