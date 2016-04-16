from script_runner import *

ds = DataScript("couchie", """
@stream('*.raw')
def test(chan,device,data):
    device.avgd.push(avg(chan[-2:]))
@stream('*.avgd')
def test2(chan,data):
    print data
""")

ds.start()
