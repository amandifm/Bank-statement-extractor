import re

DATE=r'^\d{1,2}[/-]\d{1,2}'
AMOUNT=r'[-]?\$?[\d,]+\.\d{2}-?$'


def is_date(v):
    return re.match(DATE,v.strip())


def is_amount(v):
    return re.search(AMOUNT,v)


def parse(lines):

    tx=[]
    current=None

    for line in lines:

        line=line.strip()

        if not line:
            continue

        if is_date(line):

            if current:
                tx.append(current)

            current={
                "date":"",
                "description":"",
                "amount":"",
                "balance":""
            }

            pieces=line.split()

            current["date"]=pieces[0]

            remaining=" ".join(pieces[1:])


            nums=re.findall(
                r'[\d,]+\.\d{2}-?',
                remaining
            )

            if nums:

                current["balance"]=nums[-1]

                if len(nums)>=2:
                    current["amount"]=nums[-2]

                desc=remaining

                for x in nums:
                    desc=desc.replace(x,"")

                current["description"]=desc.strip()

            else:

                current["description"]=remaining

        else:

            if current:
                current["description"]+=" "+line

    if current:
        tx.append(current)

    return tx