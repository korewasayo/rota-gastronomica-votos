import pandas as pd
import os

# muda isto pra pasta onde tão os csvs
input_folder = r"./"

# pasta de saida (vai criar e n existir)
output_folder = os.path.join(input_folder, "output_limpos")
os.makedirs(output_folder, exist_ok=True)

ficheiros_encontrados = 0

# percorre todas as pastas dentro da pasta inicial
for root, dirs, files in os.walk(input_folder):
    for file in files:
        # só apanha ficheiros csv e ignora a pasta de output
        if file.endswith(".csv") and "output_limpos" not in root:
            ficheiros_encontrados += 1

            input_path = os.path.join(root, file)

            # master a estrutura
            relative_path = os.path.relpath(root, input_folder)
            output_dir = os.path.join(output_folder, relative_path)
            os.makedirs(output_dir, exist_ok=True)

            output_path = os.path.join(output_dir, file)

            try:
                # le csv
                df = pd.read_csv(input_path)

                # converte a coluna Timestamp para datetime (se der erro mete NaT)
                df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
                
                # ordena pelo tempo (mais antigo primeiro)
                df = df.sort_values(by="Timestamp")
                
                # remove duplicados pelo email ficando com o primeiro (mais antigo)
                df_clean = df.drop_duplicates(subset="Email Address", keep="first")
                
                # guarda o ficheiro limpo
                df_clean.to_csv(output_path, index=False)

                print(f"✔ {input_path}")

            except Exception as e:
                print(f"❌ Erro em {input_path}: {e}")
# se n encontrou nada avisa
if ficheiros_encontrados == 0:
    print(" Nenhum ficheiro csv encontrado..")
else:
    print(f"{ficheiros_encontrados} ficheiros processados")