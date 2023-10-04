from bddutil import xor

class Cost:
    def __init__(self, size, value):
        self.size = size
        self.value = value

    def __str__(self):
        return str(self.value)

    def to_bitarray(self):
        val = self.value
        if val == 0:
            return [0 for i in range(self.size)]

        bits = []
        padding = []

        while val > 0:
            bits.append(val % 2)
            val >>= 1
        
        if(len(bits) < self.size):
            padding = [0 for i in range(self.size - len(bits))]

        return padding + bits[::-1]

    def to_BDD(self, C, base):
        assert self.size == len(C)

        bits = self.to_bitarray()[::-1]
        res = base.bdd.true

        for b in range(len(bits)):
            var = base.bdd.var(C[b])
            if bits[b] == 1:
                res = res & var
            else:
                res = res & (~var)

        return res

    def __eq__(self, other):
        return isinstance(other, Cost) and \
               self.size == other.size and \
               self.value == other.value

    @staticmethod
    def BDD_to_bitarray(base, C, cbdd):
        sol = list(base.bdd.pick_iter(cbdd))
        assert len(sol) == 1
        
        res_bits = [0 for c in C]
        for c in C:
            if sol[0][c] == True:
                i = C.index(c)
                res_bits[C.index(c)] = 1
        return res_bits

    @staticmethod
    def bitarray_to_cost(bits):
        res = 0
        for b in range(len(bits)):
            res += pow(2,b) * bits[b]
        return Cost(len(bits), res)   
    
    @staticmethod
    def BDD_to_cost(base, C, cbdd):
        bits = Cost.BDD_to_bitarray(base, C, cbdd)
        return Cost.bitarray_to_cost(bits)

    @staticmethod
    def add_BDD(c1, c2, C1, C2, Cout, base, carry = 0):
        c1 = Cost.BDD_to_bitarray(base, C1, c1)
        c2 = Cost.BDD_to_bitarray(base, C2, c2)

        assert len(c1) == len(c2)
        res = []

        for n in range(len(c1)):
            res.append(c1[n] ^ c2[n] ^ carry)
            carry = (c1[n] & c2[n]) | \
                    (c1[n] & carry) | \
                    (c2[n] & carry)

        return Cost.bitarray_to_cost(res).to_BDD(Cout, base)

    @staticmethod
    def subtract_BDD(c1, c2, C1, C2, Cout, base):
        c1 = Cost.BDD_to_bitarray(base, C1, c1)
        c2 = Cost.BDD_to_bitarray(base, C2, c2)
        c2 = [0 if c == 1 else 1 for c in c2]

        c1 = Cost.bitarray_to_cost(c1).to_BDD(C1, base)
        c2 = Cost.bitarray_to_cost(c2).to_BDD(C2, base)

        return Cost.add_BDD(c1,c2,C1,C2,Cout,base,carry=1)    

    @staticmethod
    def sum_check(c1, c2, cres, base):
        carry = base.bdd.false
        res = base.bdd.true

        sum_vals = []

        for n in range(base.cost_size):
            b1 = base.bdd.var(c1[n])
            b2 = base.bdd.var(c2[n])

            sum_vals.append(xor(xor(b1, (b2)), carry))
            carry = (b1 & (b2)) | \
                    (carry & xor(b1, (b2)))

            res = res & sum_vals[n].equiv(base.bdd.var(cres[n]))
        return res & (~carry) # THIS IS TO PROTECT AGAINST OVERFLOW

    @staticmethod
    def subtract_check(c1, c2, cres, base):
        carry = base.bdd.true
        res = base.bdd.true

        sum_vals = []

        for n in range(base.cost_size):
            b1 = base.bdd.var(c1[n])
            b2 = ~base.bdd.var(c2[n])

            sum_vals.append(xor(xor(b1, b2), carry))
            carry = (b1 & b2) | \
                    (carry & xor(b1, b2))
  
        res = res & sum_vals[n].equiv(base.bdd.var(cres[n]))

        # Will return false if carry produced (negative result)
        return res & carry   
 
    @staticmethod
    def LEQ(c1, c2, base):
        carry = base.bdd.true
        sum_vals = []

        # Do addition with two's complement
        # If c2 - c1 < 0, then c1 is greater, otherwise leq
        # To check c2 - c1 we do c2 + (-c1) using two's complement

        for n in range(base.cost_size):
            b1 = base.bdd.var(c2[n])
            b2 = ~base.bdd.var(c1[n])

            carry = (b1 & b2) | \
                    (carry & xor(b1, b2))

        # If carry false, then c2 - c1 < 0 and c1 is greater -> not leq
        return ~carry.equiv(base.bdd.false) 