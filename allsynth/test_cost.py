import unittest
from bddbase import BDDbase
from cost import Cost

class CostTests(unittest.TestCase):
    def setUp(self):
        self.base = BDDbase()
        size = 4
        self.base.cost_size = size
        self.C1 = ['c1_'+str(i) for i in range(size)]
        self.base.bdd.declare(*self.C1)
        self.base.C1 = self.C1

        self.C2 = ['c2_'+str(i) for i in range(size)]
        self.base.bdd.declare(*self.C2)
        self.base.C2 = self.C2

        self.C3 = ['c3_'+str(i) for i in range(size)]
        self.base.bdd.declare(*self.C3)
        self.base.C3 = self.C3

    def test_toBitArray(self):
        twelve = Cost(5,12)
        expected = [0,1,1,0,0]
        actual = twelve.to_bitarray()
        self.assertEqual(expected, actual)

    def test_bitArrayToCost(self):
        arr = [0,0,1,1,0]
        expected = Cost(5,12)
        actual = Cost.bitarray_to_cost(arr)
        self.assertEqual(expected, actual)

    def test_bddToBitArray(self):
        eleven = Cost(4,11).to_BDD(self.C1, self.base)
        actual = Cost.BDD_to_bitarray(self.base, self.C1, eleven)

        expected = [1,1,0,1]
        self.assertEqual(expected, actual)

    def test_add(self):
        five = Cost(4,5).to_BDD(self.C1, self.base)
        six = Cost(4,6).to_BDD(self.C1, self.base)

        expected = Cost(4,11)

        actual = Cost.BDD_to_cost(self.base, self.C1, Cost.add_BDD(five, six, self.C1, self.C1, self.C1, self.base))

        self.assertEqual(actual, expected)

    def test_add_bdd1(self):
        s = Cost.sum_check(self.C1, self.C2, self.C3, self.base)
        
        five = Cost(4,5).to_BDD(self.C1, self.base)
        six = Cost(4,6).to_BDD(self.C2, self.base)
        eleven = Cost(4,11).to_BDD(self.C3, self.base)

        five_sol = list(self.base.bdd.pick_iter(five))
        six_sol = list(self.base.bdd.pick_iter(six))
        eleven_sol = list(self.base.bdd.pick_iter(eleven))

        self.assertEqual(len(five_sol), 1)
        self.assertEqual(len(six_sol), 1)
        self.assertEqual(len(eleven_sol), 1)

        actual = self.base.bdd.let({**five_sol[0], **six_sol[0], **eleven_sol[0]}, s)
        expected = self.base.bdd.true

        self.assertEqual(actual, expected)

    def test_add_bdd2(self):
        s = Cost.sum_check(self.C1, self.C2, self.C3, self.base)
        
        one = Cost(4,1).to_BDD(self.C1, self.base)
        nine = Cost(4,9).to_BDD(self.C2, self.base)
        ten = Cost(4,10).to_BDD(self.C3, self.base)

        one_sol = list(self.base.bdd.pick_iter(one))
        nine_sol = list(self.base.bdd.pick_iter(nine))
        ten_sol = list(self.base.bdd.pick_iter(ten))

        self.assertEqual(len(one_sol), 1)
        self.assertEqual(len(nine_sol), 1)
        self.assertEqual(len(ten_sol), 1)

        actual = self.base.bdd.let({**one_sol[0], **nine_sol[0], **ten_sol[0]}, s)
        expected = self.base.bdd.true

        self.assertEqual(actual, expected)

    def test_add_bdd3(self):
        s = Cost.sum_check(self.C2, self.C3, self.C1, self.base)

        one = Cost(4,1).to_BDD(self.C3, self.base)
        nine = Cost(4,9).to_BDD(self.C2, self.base)
        ten = Cost(4,10).to_BDD(self.C1, self.base)

        one_sol = list(self.base.bdd.pick_iter(one))
        nine_sol = list(self.base.bdd.pick_iter(nine))
        ten_sol = list(self.base.bdd.pick_iter(ten))

        self.assertEqual(len(one_sol), 1)
        self.assertEqual(len(nine_sol), 1)
        self.assertEqual(len(ten_sol), 1)

        actual = self.base.bdd.let({**one_sol[0], **nine_sol[0], **ten_sol[0]}, s)
        expected = self.base.bdd.true

        self.assertEqual(actual, expected)

    def test_subtract_bdd(self):
        s = Cost.subtract_check(self.C2, self.C1, self.C3, self.base)


        five = Cost(4,5).to_BDD(self.C1, self.base)
        six = Cost(4,6).to_BDD(self.C2, self.base)
        one = Cost(4,1).to_BDD(self.C3, self.base)

        one_bdd = Cost.subtract_BDD(six, five, self.C2, self.C1, self.C3, self.base)

        five_sol = list(self.base.bdd.pick_iter(five))
        six_sol = list(self.base.bdd.pick_iter(six))
        one_sol = list(self.base.bdd.pick_iter(one))

        self.assertTrue(one_sol[0] == next(self.base.bdd.pick_iter(one_bdd)))

        self.assertEqual(len(five_sol), 1)
        self.assertEqual(len(six_sol), 1)
        self.assertEqual(len(one_sol), 1)

        actual = self.base.bdd.let({**six_sol[0] , **five_sol[0], **one_sol[0]}, s)


        expected = self.base.bdd.true

        self.assertEqual(actual, expected)
        
    def test_leq1(self):
        l = Cost.LEQ(self.C1, self.C2, self.base)

        five_c1 = Cost(4,5).to_BDD(self.C1, self.base)
        five_c2 = Cost(4,5).to_BDD(self.C2, self.base)

        six_c1 = Cost(4,6).to_BDD(self.C1, self.base)
        six_c2 = Cost(4,6).to_BDD(self.C2, self.base)

        five_sol_c1 = list(self.base.bdd.pick_iter(five_c1))
        five_sol_c2 = list(self.base.bdd.pick_iter(five_c2))

        six_sol_c1 = list(self.base.bdd.pick_iter(six_c1))
        six_sol_c2 = list(self.base.bdd.pick_iter(six_c2))
        
        actual = self.base.bdd.let({**five_sol_c1[0], **six_sol_c2[0]}, l)
        expected = self.base.bdd.true
        self.assertEqual(actual, expected)

        actual = self.base.bdd.let({**five_sol_c2[0], **six_sol_c1[0]}, l)
        expected = self.base.bdd.false
        self.assertEqual(actual, expected)

if __name__ == '__main__':
    unittest.main()