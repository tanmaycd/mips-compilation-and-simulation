.data
    val1: .word 5
    val2: .word 5
  
.text
    lw $t0, val1
    lw $t1, val2
    addi $t2, $t0, 10
    beq $t0, $t1, equal_case
    sub $t3, $t0, $t1
    j end
equal_case:
    add $t3, $t0, $t1
  
end: