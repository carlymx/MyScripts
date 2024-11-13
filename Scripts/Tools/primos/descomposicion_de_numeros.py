def encontrar_particiones(n):
    def particionar(n, max_num, actual=[]):
        if n == 0:
            print(actual)  # Imprime una de las particiones
        else:
            for i in range(min(n, max_num), 0, -1):
                particionar(n - i, i, actual + [i])

# Ejemplo de uso
numero = int(input("Introduce un número: "))
encontrar_particiones(numero)
