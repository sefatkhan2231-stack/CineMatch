# check whether a number is Strong number or not
n = int(input('Enter a number:'))

total = 0

for i in range(1, n):
    if n % i == 0:
        total += i

if total == n:
    print(f'{n} is Perfect number')
else:
    print(f'{n} is not Perfect number')

# print all Strong numbers between 1 to n
n = int(input('Enter a number:'))

strong = []

for i in range(1, n + 1):
    temp = i
    total = 0

    while temp > 0:
        lastDigit = temp % 10

        fact = 1
        for j in range(1, lastDigit + 1):
            fact *= j

        total += fact
        temp //= 10

    if total == i:
        strong.append(i)

print(strong)

# print Fibonacci series up to n terms
n = int(input('Enter a number:'))

fib = []

a, b = 0, 1

for i in range(1, n):
    fib.append(a)
    a, b = b, a + b

print(fib)

# find one’s complement of a binary number
n = str(input('Enter a number:'))

onesComp = ''
error = 0

for i in n:
    if i == '0':
        onesComp += '1'
    elif i == '1':
        onesComp += '0'
    else:
        print('Invalid Input')
        error = 1
        break

if error == 0:
    print(f'Original binary = {n}')
    print(f'Ones complement = {onesComp}')

# find two’s complement of a binary number
n = str(input('Enter a number:'))

onesComp = ''
twosComp = ''
error = 0

for i in n:
    if i == '0':
        onesComp += '1'
    elif i == '1':
        onesComp += '0'
    else:
        print('Invalid Input')
        error = 1
        break

twosComp = str(int(onesComp) + 1)

if error == 0:
    print(f'Original binary = {n}')
    print(f'Ones complement = {onesComp}')
    print(f'Twos complement = {twosComp}')

# convert Binary to Octal number system
n = int(input('Enter a number:'))

octalConstant = [0, 1, 10, 11, 100, 101, 110, 111]

octal = 0
place = 1
tempBinary = n

while tempBinary != 0:
    digit = tempBinary % 1000

    for i in range(8):
        if octalConstant[i] == digit:
            octal = (i * place) + octal
            break

    tempBinary //= 1000
    place *= 10

print(f'Original binary number = {n}')
print(f'Octal number = {octal}')

# convert Binary to Decimal number system
n = int(input('Enter a number:'))

decimal = 0
place = 0
tempBinary = n

while tempBinary != 0:

    if tempBinary % 10 == 1:
        decimal += 2 ** place

    place += 1
    tempBinary //= 10

print(f'Original binary number = {n}')
print(f'Octal number = {decimal}')