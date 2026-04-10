"""
Main driver for Pascal → Alpha AXP Compiler.

Usage:
  python compiler.py <input.pas> [-o output.s] [-v]

Pipeline:
  1. Lex    → token stream
  2. Parse  → AST
  3. Analyse → scopes + offsets
  4. CodeGen → Alpha assembly text
"""

import sys
import os
import argparse

# Make sure we can import sibling modules
sys.path.insert(0, os.path.dirname(__file__))

from lexer import Lexer, LexerError
from parser import Parser, ParseError
from semantic import SemanticAnalyser, SemanticError
from codegen import AlphaCodeGen, CodeGenError

BANNER = """
╔══════════════════════════════════════════════════╗
║   Pascal → DEC Alpha AXP Compiler  (v1.0)        ║
║   Emits GNU assembler (.s) for Alpha AXP ISA     ║
╚══════════════════════════════════════════════════╝
"""

def compile_source(source: str, filename: str = '<input>',
                   verbose: bool = False) -> str:
    """
    Full compilation pipeline.
    Returns the Alpha assembly text, or raises on error.
    """

    # ── Stage 1: Lex ─────────────────────────────────────────────────────
    if verbose:
        print(f"[1/4] Lexing {filename} ...")
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    if verbose:
        print(f"      {len(tokens)} tokens")
        for tok in tokens[:20]:
            print(f"      {tok}")
        if len(tokens) > 20:
            print(f"      ... ({len(tokens) - 20} more)")

    # ── Stage 2: Parse ────────────────────────────────────────────────────
    if verbose:
        print(f"[2/4] Parsing ...")
    parser = Parser(tokens)
    ast = parser.parse_program()
    if verbose:
        print(f"      Program: '{ast.name}'")
        print(f"      {len(ast.var_decls)} var decls, "
              f"{len(ast.procedures)} procedures, "
              f"{len(ast.body.stmts)} top-level statements")

    # ── Stage 3: Semantic analysis ────────────────────────────────────────
    if verbose:
        print(f"[3/4] Semantic analysis ...")
    analyser = SemanticAnalyser()
    global_scope = analyser.analyse(ast)
    if verbose:
        print(f"      Scopes: {list(analyser.scopes.keys())}")
        for name, sym in global_scope.symbols.items():
            print(f"      Global: {name} : {sym.type_}")

    # ── Stage 4: Code generation ──────────────────────────────────────────
    if verbose:
        print(f"[4/4] Generating Alpha AXP assembly ...")
    codegen = AlphaCodeGen(analyser.scopes)
    asm = codegen.gen_program(ast)
    if verbose:
        lines = asm.count('\n')
        print(f"      Generated {lines} lines of Alpha assembly")

    return asm

def main():
    print(BANNER)
    ap = argparse.ArgumentParser(
        description='Pascal → DEC Alpha AXP compiler')
    ap.add_argument('input', help='Input Pascal source file (.pas)')
    ap.add_argument('-o', '--output', help='Output assembly file (.s)')
    ap.add_argument('-v', '--verbose', action='store_true',
                    help='Show compilation pipeline details')
    args = ap.parse_args()

    # Read source
    try:
        with open(args.input, 'r') as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Output filename
    out_file = args.output
    if not out_file:
        base = os.path.splitext(args.input)[0]
        out_file = base + '.s'

    # Compile
    try:
        asm = compile_source(source, args.input, verbose=args.verbose)
    except LexerError as e:
        print(f"\nLexer Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ParseError as e:
        print(f"\nParse Error: {e}", file=sys.stderr)
        sys.exit(1)
    except SemanticError as e:
        print(f"\nSemantic Error: {e}", file=sys.stderr)
        sys.exit(1)
    except CodeGenError as e:
        print(f"\nCode Generation Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Write output
    with open(out_file, 'w') as f:
        f.write(asm)

    print(f"   Compiled '{args.input}' → '{out_file}'")
    print(f"   To assemble (requires Alpha binutils):")
    print(f"     as -o {os.path.splitext(out_file)[0]}.o {out_file}")
    print(f"   To link (requires Alpha libc):")
    print(f"     ld -o {os.path.splitext(out_file)[0]} {os.path.splitext(out_file)[0]}.o -lc")
    print(f"   To run (requires QEMU Alpha or real hardware):")
    print(f"     qemu-alpha {os.path.splitext(out_file)[0]}")


if __name__ == '__main__':
    main()