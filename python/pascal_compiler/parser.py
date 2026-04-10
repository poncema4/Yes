"""
Recursive-descent parser for Pascal → Alpha Compiler.
Consumes tokens from the lexer and builds an AST.
"""

from typing import List, Optional
from lexer import Token, TokenType
from ast_nodes import *

class ParseError(Exception):
    def __init__(self, msg, token):
        super().__init__(f"Parse error at line {token.line}: {msg} (got {token.type.name} '{token.value}')")
        self.token = token

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    # ── Token navigation ──────────────────────────────────────────────────

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def peek_type(self) -> TokenType:
        return self.tokens[self.pos].type

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        if tok.type != TokenType.EOF:
            self.pos += 1
        return tok

    def expect(self, tt: TokenType) -> Token:
        tok = self.peek()
        if tok.type != tt:
            raise ParseError(f"Expected {tt.name}", tok)
        return self.advance()

    def match(self, *types) -> bool:
        return self.peek_type() in types

    def consume_if(self, tt: TokenType) -> Optional[Token]:
        if self.match(tt):
            return self.advance()
        return None

    # ── Top-level ─────────────────────────────────────────────────────────

    def parse_program(self) -> Program:
        self.expect(TokenType.PROGRAM)
        name = self.expect(TokenType.IDENT).value
        if self.match(TokenType.LPAREN):   # optional param list (ignore)
            self.advance()
            while not self.match(TokenType.RPAREN, TokenType.EOF):
                self.advance()
            self.expect(TokenType.RPAREN)
        self.expect(TokenType.SEMICOLON)

        var_decls = []
        procedures = []

        while self.match(TokenType.VAR, TokenType.PROCEDURE, TokenType.FUNCTION):
            if self.match(TokenType.VAR):
                var_decls.extend(self.parse_var_section())
            else:
                procedures.append(self.parse_proc_or_func())

        body = self.parse_compound_stmt()
        self.expect(TokenType.DOT)
        return Program(name=name, var_decls=var_decls, procedures=procedures, body=body)

    # ── Declarations ──────────────────────────────────────────────────────

    def parse_var_section(self) -> List[VarDecl]:
        self.expect(TokenType.VAR)
        decls = []
        while self.match(TokenType.IDENT):
            decls.append(self.parse_var_decl())
        return decls

    def parse_var_decl(self) -> VarDecl:
        names = [self.expect(TokenType.IDENT).value]
        while self.consume_if(TokenType.COMMA):
            names.append(self.expect(TokenType.IDENT).value)
        self.expect(TokenType.COLON)
        t = self.parse_type()
        self.expect(TokenType.SEMICOLON)
        return VarDecl(names=names, type_=t)

    def parse_type(self) -> TypeNode:
        if self.match(TokenType.INTEGER_T):
            self.advance(); return SimpleType('integer')
        elif self.match(TokenType.REAL_T):
            self.advance(); return SimpleType('real')
        elif self.match(TokenType.BOOLEAN_T):
            self.advance(); return SimpleType('boolean')
        elif self.match(TokenType.CHAR_T):
            self.advance(); return SimpleType('char')
        elif self.match(TokenType.STRING_T):
            self.advance(); return SimpleType('string')
        elif self.match(TokenType.ARRAY):
            return self.parse_array_type()
        elif self.match(TokenType.IDENT):
            name = self.advance().value
            return SimpleType(name)
        else:
            raise ParseError("Expected type", self.peek())

    def parse_array_type(self) -> ArrayType:
        self.expect(TokenType.ARRAY)
        self.expect(TokenType.LBRACKET)
        low = int(self.expect(TokenType.INTEGER).value)
        self.expect(TokenType.DOTDOT)
        high = int(self.expect(TokenType.INTEGER).value)
        self.expect(TokenType.RBRACKET)
        self.expect(TokenType.OF)
        elem = self.parse_type()
        return ArrayType(low=low, high=high, element_type=elem)

    def parse_param_list(self) -> List[ParamDecl]:
        params = []
        self.expect(TokenType.LPAREN)
        while not self.match(TokenType.RPAREN, TokenType.EOF):
            by_ref = bool(self.consume_if(TokenType.VAR))
            names = [self.expect(TokenType.IDENT).value]
            while self.consume_if(TokenType.COMMA):
                names.append(self.expect(TokenType.IDENT).value)
            self.expect(TokenType.COLON)
            t = self.parse_type()
            params.append(ParamDecl(names=names, type_=t, by_ref=by_ref))
            self.consume_if(TokenType.SEMICOLON)
        self.expect(TokenType.RPAREN)
        return params

    def parse_proc_or_func(self) -> ProcDecl:
        is_func = self.match(TokenType.FUNCTION)
        self.advance()
        name = self.expect(TokenType.IDENT).value
        params = []
        if self.match(TokenType.LPAREN):
            params = self.parse_param_list()
        return_type = None
        if is_func:
            self.expect(TokenType.COLON)
            return_type = self.parse_type()
        self.expect(TokenType.SEMICOLON)

        var_decls = []
        nested = []
        while self.match(TokenType.VAR, TokenType.PROCEDURE, TokenType.FUNCTION):
            if self.match(TokenType.VAR):
                var_decls.extend(self.parse_var_section())
            else:
                nested.append(self.parse_proc_or_func())

        body = self.parse_compound_stmt()
        self.expect(TokenType.SEMICOLON)
        return ProcDecl(name=name, params=params, return_type=return_type,
                        var_decls=var_decls, body=body, nested=nested)

    # ── Statements ────────────────────────────────────────────────────────

    def parse_compound_stmt(self) -> Block:
        self.expect(TokenType.BEGIN)
        stmts = []
        while not self.match(TokenType.END, TokenType.EOF):
            stmts.append(self.parse_stmt())
            self.consume_if(TokenType.SEMICOLON)
        self.expect(TokenType.END)
        return Block(stmts=stmts)

    def parse_stmt(self) -> Stmt:
        tt = self.peek_type()

        if tt == TokenType.BEGIN:
            return self.parse_compound_stmt()
        elif tt == TokenType.IF:
            return self.parse_if()
        elif tt == TokenType.WHILE:
            return self.parse_while()
        elif tt == TokenType.FOR:
            return self.parse_for()
        elif tt == TokenType.REPEAT:
            return self.parse_repeat()
        elif tt in (TokenType.WRITELN, TokenType.WRITE):
            return self.parse_write()
        elif tt in (TokenType.READLN, TokenType.READ):
            return self.parse_read()
        elif tt == TokenType.IDENT:
            return self.parse_assign_or_call()
        else:
            return EmptyStmt()

    def parse_if(self) -> IfStmt:
        self.expect(TokenType.IF)
        cond = self.parse_expr()
        self.expect(TokenType.THEN)
        then_b = self.parse_stmt()
        else_b = None
        if self.consume_if(TokenType.ELSE):
            else_b = self.parse_stmt()
        return IfStmt(condition=cond, then_branch=then_b, else_branch=else_b)

    def parse_while(self) -> WhileStmt:
        self.expect(TokenType.WHILE)
        cond = self.parse_expr()
        self.expect(TokenType.DO)
        body = self.parse_stmt()
        return WhileStmt(condition=cond, body=body)

    def parse_for(self) -> ForStmt:
        self.expect(TokenType.FOR)
        var = self.expect(TokenType.IDENT).value
        self.expect(TokenType.ASSIGN)
        start = self.parse_expr()
        downto = bool(self.consume_if(TokenType.DOWNTO))
        if not downto:
            self.expect(TokenType.TO)
        stop = self.parse_expr()
        self.expect(TokenType.DO)
        body = self.parse_stmt()
        return ForStmt(var=var, start=start, stop=stop, downto=downto, body=body)

    def parse_repeat(self) -> RepeatStmt:
        self.expect(TokenType.REPEAT)
        stmts = []
        while not self.match(TokenType.UNTIL, TokenType.EOF):
            stmts.append(self.parse_stmt())
            self.consume_if(TokenType.SEMICOLON)
        self.expect(TokenType.UNTIL)
        cond = self.parse_expr()
        return RepeatStmt(body=stmts, condition=cond)

    def parse_write(self) -> WritelnStmt:
        newline = self.peek_type() == TokenType.WRITELN
        self.advance()
        args = []
        if self.consume_if(TokenType.LPAREN):
            args.append(self.parse_expr())
            while self.consume_if(TokenType.COMMA):
                args.append(self.parse_expr())
            self.expect(TokenType.RPAREN)
        return WritelnStmt(args=args, newline=newline)

    def parse_read(self) -> ReadlnStmt:
        self.advance()
        args = []
        if self.consume_if(TokenType.LPAREN):
            args.append(self.parse_expr())
            while self.consume_if(TokenType.COMMA):
                args.append(self.parse_expr())
            self.expect(TokenType.RPAREN)
        return ReadlnStmt(args=args)

    def parse_assign_or_call(self) -> Stmt:
        name = self.expect(TokenType.IDENT).value
        if self.match(TokenType.ASSIGN):
            self.advance()
            val = self.parse_expr()
            return Assign(target=Var(name), value=val)
        elif self.match(TokenType.LBRACKET):
            self.advance()
            idx = self.parse_expr()
            self.expect(TokenType.RBRACKET)
            self.expect(TokenType.ASSIGN)
            val = self.parse_expr()
            return Assign(target=ArrayAccess(Var(name), idx), value=val)
        elif self.match(TokenType.LPAREN):
            self.advance()
            args = []
            if not self.match(TokenType.RPAREN):
                args.append(self.parse_expr())
                while self.consume_if(TokenType.COMMA):
                    args.append(self.parse_expr())
            self.expect(TokenType.RPAREN)
            return ProcCall(name=name, args=args)
        else:
            return ProcCall(name=name, args=[])

    # ── Expressions ───────────────────────────────────────────────────────

    def parse_expr(self) -> Expr:
        return self.parse_or_expr()

    def parse_or_expr(self) -> Expr:
        left = self.parse_and_expr()
        while self.match(TokenType.OR):
            op = self.advance().value.lower()
            right = self.parse_and_expr()
            left = BinOp(op=op, left=left, right=right)
        return left

    def parse_and_expr(self) -> Expr:
        left = self.parse_rel_expr()
        while self.match(TokenType.AND):
            op = self.advance().value.lower()
            right = self.parse_rel_expr()
            left = BinOp(op=op, left=left, right=right)
        return left

    def parse_rel_expr(self) -> Expr:
        left = self.parse_add_expr()
        rel = {TokenType.EQ:'=', TokenType.NEQ:'<>', TokenType.LT:'<',
               TokenType.LE:'<=', TokenType.GT:'>', TokenType.GE:'>='}
        if self.peek_type() in rel:
            op = rel[self.advance().type]
            right = self.parse_add_expr()
            return BinOp(op=op, left=left, right=right)
        return left

    def parse_add_expr(self) -> Expr:
        left = self.parse_mul_expr()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op = self.advance().value
            right = self.parse_mul_expr()
            left = BinOp(op=op, left=left, right=right)
        return left

    def parse_mul_expr(self) -> Expr:
        left = self.parse_unary_expr()
        mul_ops = {TokenType.STAR:'*', TokenType.SLASH:'/',
                   TokenType.DIV:'div', TokenType.MOD:'mod'}
        while self.peek_type() in mul_ops:
            op = mul_ops[self.advance().type]
            right = self.parse_unary_expr()
            left = BinOp(op=op, left=left, right=right)
        return left

    def parse_unary_expr(self) -> Expr:
        if self.match(TokenType.MINUS):
            self.advance()
            return UnaryOp(op='-', operand=self.parse_primary())
        if self.match(TokenType.NOT):
            self.advance()
            return UnaryOp(op='not', operand=self.parse_primary())
        return self.parse_primary()

    def parse_primary(self) -> Expr:
        tok = self.peek()
        tt = tok.type

        if tt == TokenType.INTEGER:
            self.advance()
            return IntLit(int(tok.value))
        elif tt == TokenType.REAL:
            self.advance()
            return RealLit(float(tok.value))
        elif tt == TokenType.STRING:
            self.advance()
            return StrLit(tok.value)
        elif tt == TokenType.TRUE:
            self.advance(); return BoolLit(True)
        elif tt == TokenType.FALSE:
            self.advance(); return BoolLit(False)
        elif tt == TokenType.LPAREN:
            self.advance()
            e = self.parse_expr()
            self.expect(TokenType.RPAREN)
            return e
        elif tt == TokenType.IDENT:
            name = self.advance().value
            if self.match(TokenType.LPAREN):
                self.advance()
                args = []
                if not self.match(TokenType.RPAREN):
                    args.append(self.parse_expr())
                    while self.consume_if(TokenType.COMMA):
                        args.append(self.parse_expr())
                self.expect(TokenType.RPAREN)
                return FuncCall(name=name, args=args)
            elif self.match(TokenType.LBRACKET):
                self.advance()
                idx = self.parse_expr()
                self.expect(TokenType.RBRACKET)
                return ArrayAccess(Var(name), idx)
            else:
                return Var(name)
        else:
            raise ParseError("Expected expression", tok)