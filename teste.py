from random import choice
import string
import math

option = int(input("[1]Números e letras \n[2]Números, letras e pontos \n[3]Números \n"))

match option: 
    case 1:
        password_lenght = 0 
        while password_lenght < 3: 
            password_lenght=int(input("What a Password Size? "))
        if password_lenght < 3:
            print("The value is not acepted. The minimum values is 3.")

        character = string.ascii_letters + string.digits 
        secure_password = ''
        for i in range(password_lenght):
         secure_password += choice(character)
        print("The password is: ", secure_password)
    case 2:
        produção = "working..."
        print(produção)
    case 3:
        password_lenght = 0 
        while password_lenght < 3: 
            password_lenght=int(input("What a Password Size? "))
        if password_lenght < 3:
            print("The value is not acepted. The minimum values is 3.")

        character = string.ascii_letters + string.digits + string.punctuation
        secure_password = ''
        for i in range(password_lenght):
         secure_password += choice(character)
        print("The password is: ", secure_password)