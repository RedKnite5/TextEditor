

class A:
    def __getitem__(self, item):
        print(item)


a = A()
a[1]
a[:0]
a[1:2]
a[1:2:3]
a[::2]