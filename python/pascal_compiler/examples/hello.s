	.text
	.align 3

	# === Runtime support stubs ===

	# __print_int(A0=value)
__print_int:
	lda	sp, -16(sp)
	stq	ra, 8(sp)
	mov	a0, a1
	lda	a0, _fmt_int
	bsr	ra, printf
	ldq	ra, 8(sp)
	lda	sp, 16(sp)
	ret	zero, (ra), 1

	# __print_str(A0=ptr)
__print_str:
	lda	sp, -16(sp)
	stq	ra, 8(sp)
	bsr	ra, printf
	ldq	ra, 8(sp)
	lda	sp, 16(sp)
	ret	zero, (ra), 1

	# __print_newline()
__print_newline:
	lda	sp, -16(sp)
	stq	ra, 8(sp)
	lda	a0, _newline
	bsr	ra, printf
	ldq	ra, 8(sp)
	lda	sp, 16(sp)
	ret	zero, (ra), 1

	# __read_int() -> V0
__read_int:
	lda	sp, -32(sp)
	stq	ra, 24(sp)
	lda	a0, _fmt_int_in
	lda	a1, 16(sp)
	bsr	ra, scanf
	ldq	v0, 16(sp)
	ldq	ra, 24(sp)
	lda	sp, 32(sp)
	ret	zero, (ra), 1

	# __divq(A0, A1) -> V0  (A0 div A1)
__divq:
	lda	sp, -32(sp)
	stq	ra, 24(sp)
	bsr	ra, __os_divq
	ldq	ra, 24(sp)
	lda	sp, 32(sp)
	ret	zero, (ra), 1

	# __modq(A0, A1) -> V0  (A0 mod A1)
__modq:
	lda	sp, -32(sp)
	stq	ra, 24(sp)
	bsr	ra, __os_modq
	ldq	ra, 24(sp)
	lda	sp, 32(sp)
	ret	zero, (ra), 1

	# === End runtime stubs ===


	# ─── Main program entry point ───
	.globl	_start
_start:
	lda	sp, -32(sp)
	stq	ra, 24(sp)
	stq	fp, 16(sp)
	mov	sp, fp
	# writeln
	lda	a0, STR1
	bsr	ra, __print_str
	bsr	ra, __print_newline
	# writeln
	lda	a0, STR2
	bsr	ra, __print_str
	bsr	ra, __print_newline
	mov	fp, sp
	ldq	ra, 24(sp)
	ldq	fp, 16(sp)
	lda	sp, 32(sp)
	# exit(0) via PALcode
	mov	zero, a0
	call_pal	0x0001

	.data
	.align 3
STR1:
	.asciz	"Hello from the Alpha processor!"
STR2:
	.asciz	"Pascal → Alpha AXP compiler demo"

_fmt_int:
	.asciz	"%ld"
_fmt_int_in:
	.asciz	"%ld"
_newline:
	.asciz	"\n"