from datetime import datetime as dtime

cur = dtime.now().time()

def process(elem_pair:list):
    print(elem_pair[1])

mylist = []
mylist.append(("a", 0, "polsi"))
mylist.append(("b", 1, "erwe"))
mylist.append(("c", 2, "gfged"))
mylist.append(("d", 3, "hjyj"))
mylist.append(("e", 4, "hty"))

process(elem_pair=mylist[3])