"""
Lexer for Pascal → Alpha Compiler
Tokenizes Pascal source code into a stream of tokens.
"""

import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional

class TokenType(Enum):
    # Literals
    INTEGER    = auto()
    REAL       = auto()
    STRING     = auto()
    BOOLEAN    = auto()

    # Identifiers & Keywords
    IDENT      = auto()
    PROGRAM    = auto()
    VAR        = auto()
    BEGIN      = auto()
    END        = auto()
    IF         = auto()
    THEN       = auto()
    ELSE       = auto()
    WHILE      = auto()
    DO         = auto()
    FOR        = auto()
    TO         = auto()
    DOWNTO     = auto()
    PROCEDURE  = auto()
    FUNCTION   = auto()
    WRITELN    = auto()
    WRITE      = auto()
    READLN     = auto()
    READ       = auto()
    DIV        = auto()
    MOD        = auto()
    AND        = auto()
    OR         = auto()
    NOT        = auto()
    TRUE       = auto()
    FALSE      = auto()
    INTEGER_T  = auto()  # type keyword
    REAL_T     = auto()  # type keyword
    BOOLEAN_T  = auto()  # type keyword
    CHAR_T     = auto()  # type keyword
    STRING_T   = auto()  # type keyword
    ARRAY      = auto()
    OF         = auto()
    RECORD     = auto()
    REPEAT     = auto()
    UNTIL      = auto()

    # Operators
    ASSIGN     = auto()  # :=
    PLUS       = auto()
    MINUS      = auto()
    STAR       = auto()
    SLASH      = auto()
    EQ         = auto()  # =
    NEQ        = auto()  # <>
    LT         = auto()  # <
    LE         = auto()  # <=
    GT         = auto()  # >
    GE         = auto()  # >=

    # Punctuation
    LPAREN     = auto()
    RPAREN     = auto()
    LBRACKET   = auto()
    RBRACKET   = auto()
    SEMICOLON  = auto()
    COLON      = auto()
    COMMA      = auto()
    DOT        = auto()
    DOTDOT     = auto()

    # Special
    EOF        = auto()

KEYWORDS = {
    'program':   TokenType.PROGRAM,
    'var':       TokenType.VAR,
    'begin':     TokenType.BEGIN,
    'end':       TokenType.END,
    'if':        TokenType.IF,
    'then':      TokenType.THEN,
    'else':      TokenType.ELSE,
    'while':     TokenType.WHILE,
    'do':        TokenType.DO,
    'for':       TokenType.FOR,
    'to':        TokenType.TO,
    'downto':    TokenType.DOWNTO,
    'procedure': TokenType.PROCEDURE,
    'function':  TokenType.FUNCTION,
    'writeln':   TokenType.WRITELN,
    'write':     TokenType.WRITE,
    'readln':    TokenType.READLN,
    'read':      TokenType.READ,
    'div':       TokenType.DIV,
    'mod':       TokenType.MOD,
    'and':       TokenType.AND,
    'or':        TokenType.OR,
    'not':       TokenType.NOT,
    'true':      TokenType.TRUE,
    'false':     TokenType.FALSE,
    'integer':   TokenType.INTEGER_T,
    'real':      TokenType.REAL_T,
    'boolean':   TokenType.BOOLEAN_T,
    'char':      TokenType.CHAR_T,
    'string':    TokenType.STRING_T,
    'array':     TokenType.ARRAY,
    'of':        TokenType.OF,
    'record':    TokenType.RECORD,
    'repeat':    TokenType.REPEAT,
    'until':     TokenType.UNTIL,
}

@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, line={self.line})"

class LexerError(Exception):
    def __init__(self, msg, line, col):
        super().__init__(f"Lexer error at line {line}, col {col}: {msg}")
        self.line = line
        self.col = col

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []

    def error(self, msg):
        raise LexerError(msg, self.line, self.col)

    def peek(self, offset=0) -> Optional[str]:
        p = self.pos + offset
        if p < len(self.source):
            return self.source[p]
        return None

    def advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def skip_whitespace_and_comments(self):
        while self.pos < len(self.source):
            ch = self.peek()
            if ch in (' ', '\t', '\r', '\n'):
                self.advance()
            elif ch == '{':
                # { ... } comment
                self.advance()
                while self.pos < len(self.source) and self.peek() != '}':
                    self.advance()
                if self.pos >= len(self.source):
                    self.error("Unterminated comment")
                self.advance()  # consume '}'
            elif ch == '(' and self.peek(1) == '*':
                # (* ... *) comment
                self.advance(); self.advance()
                while self.pos < len(self.source):
                    if self.peek() == '*' and self.peek(1) == ')':
                        self.advance(); self.advance()
                        break
                    self.advance()
            else:
                break

    def read_number(self) -> Token:
        start_line, start_col = self.line, self.col
        num = ''
        is_real = False
        while self.peek() and self.peek().isdigit():
            num += self.advance()
        if self.peek() == '.' and self.peek(1) and self.peek(1).isdigit():
            is_real = True
            num += self.advance()  # '.'
            while self.peek() and self.peek().isdigit():
                num += self.advance()
        tt = TokenType.REAL if is_real else TokenType.INTEGER
        return Token(tt, num, start_line, start_col)

    def read_string(self) -> Token:
        start_line, start_col = self.line, self.col
        self.advance()  # opening '
        s = ''
        while self.pos < len(self.source):
            ch = self.peek()
            if ch == "'":
                self.advance()
                if self.peek() == "'":  # escaped quote ''
                    s += "'"
                    self.advance()
                else:
                    break
            else:
                s += self.advance()
        return Token(TokenType.STRING, s, start_line, start_col)

    def read_ident_or_keyword(self) -> Token:
        start_line, start_col = self.line, self.col
        word = ''
        while self.peek() and (self.peek().isalnum() or self.peek() == '_'):
            word += self.advance()
        lower = word.lower()
        tt = KEYWORDS.get(lower, TokenType.IDENT)
        return Token(tt, word, start_line, start_col)

    def tokenize(self) -> List[Token]:
        while True:
            self.skip_whitespace_and_comments()
            if self.pos >= len(self.source):
                self.tokens.append(Token(TokenType.EOF, '', self.line, self.col))
                break

            line, col = self.line, self.col
            ch = self.peek()

            if ch.isdigit():
                self.tokens.append(self.read_number())
            elif ch == "'":
                self.tokens.append(self.read_string())
            elif ch.isalpha() or ch == '_':
                self.tokens.append(self.read_ident_or_keyword())
            elif ch == ':':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.ASSIGN, ':=', line, col))
                else:
                    self.tokens.append(Token(TokenType.COLON, ':', line, col))
            elif ch == '<':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.LE, '<=', line, col))
                elif self.peek() == '>':
                    self.advance()
                    self.tokens.append(Token(TokenType.NEQ, '<>', line, col))
                else:
                    self.tokens.append(Token(TokenType.LT, '<', line, col))
            elif ch == '>':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.GE, '>=', line, col))
                else:
                    self.tokens.append(Token(TokenType.GT, '>', line, col))
            elif ch == '.':
                self.advance()
                if self.peek() == '.':
                    self.advance()
                    self.tokens.append(Token(TokenType.DOTDOT, '..', line, col))
                else:
                    self.tokens.append(Token(TokenType.DOT, '.', line, col))
            else:
                simple = {
                    '+': TokenType.PLUS,    '-': TokenType.MINUS,
                    '*': TokenType.STAR,    '/': TokenType.SLASH,
                    '=': TokenType.EQ,      '(': TokenType.LPAREN,
                    ')': TokenType.RPAREN,  '[': TokenType.LBRACKET,
                    ']': TokenType.RBRACKET,';': TokenType.SEMICOLON,
                    ',': TokenType.COMMA,
                }
                if ch in simple:
                    self.advance()
                    self.tokens.append(Token(simple[ch], ch, line, col))
                else:
                    self.error(f"Unknown character: {ch!r}")

        return self.tokens