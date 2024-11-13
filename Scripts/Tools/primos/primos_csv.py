import csv
import os
import gc
import sys
import time

# Función para verificar si un número es primo
def es_primo(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

# Función para sumar las cifras de un número
def suma_cifras(n):
    return sum(int(digit) for digit in str(n))

# Variable para indicar el último número a calcular
primer_numero = 277873073
ultimo_numero = 10000000000000000000000000000000000000000000000000000000000000000000000000000000000  # Puedes cambiar este valor

# Nombre del archivo CSV
nombre_archivo = "primo_suma.csv"

# Crear el archivo CSV si no existe, y añadir los encabezados
if not os.path.exists(nombre_archivo):
    with open(nombre_archivo, mode='w', newline='') as archivo:
        escritor = csv.writer(archivo, delimiter='\t')
        escritor.writerow(["Suma", "Número Primo"])

# Bucle principal para recorrer los números hasta el último número especificado
for numero in range(2, ultimo_numero + 1):
    if es_primo(numero):
        suma = suma_cifras(numero)

        # Mostrar en pantalla el número primo y la suma sobre la misma línea
        sys.stdout.write(f"\r{suma} - {numero}")
        sys.stdout.flush()
        #time.sleep(0.1)  # Pausa para visualizar el cambio en la misma línea

        # Si la suma de las cifras es 73, escribir en el archivo CSV
        if suma == 73:
            # Escribir en el archivo CSV
            with open(nombre_archivo, mode='a', newline='') as archivo:
                escritor = csv.writer(archivo, delimiter='\t')
                escritor.writerow([suma, numero])

            # Mostrar en pantalla el número primo y la suma sobre la misma línea
            sys.stdout.write(f"\r{suma} - {numero}\n")
            sys.stdout.flush()
            time.sleep(0.1)  # Pausa para visualizar el cambio en la misma línea

        # Purga de memoria RAM no utilizada
        gc.collect()

print(f"\nProceso completado. Los resultados se guardaron en {nombre_archivo}.")
