from flask import Flask, render_template, request, redirect, url_for
from jinja2 import Undefined
import os
import numpy as np


app = Flask(__name__)

# Fungsi menghitung kapasitor seri dan paralel
def hitung_kapasitor_seri(kapasitor_list):
    try:
        total = sum([1 / c for c in kapasitor_list])
        return 1 / total if total != 0 else 0
    except:
        return 0

def hitung_kapasitor_paralel(kapasitor_list):
    return sum(kapasitor_list)

def hitung_kirchhoff_1loop(resistors, V):
    # Hitung total resistansi seri/paralel (anggap seri sederhana di sini)
    R_total = sum(resistors)
    if R_total == 0:
        return 0
    I = V / R_total
    return I

def hitung_kirchhoff_2loop(r1, r2, r3, r4, r5, r6, v1, v2):
    # Sistem persamaan 2 loop, variabel I1 dan I2 (arus loop 1 dan 2)
    # Rangkaian contoh (R1-R6) + V1,V2
    # Persamaan contoh:
    # (R1 + R3 + R4)*I1 - R4*I2 = V1
    # -R4*I1 + (R2 + R5 + R4)*I2 = V2
    try:
        A = [[r1 + r3 + r4, -r4],
             [-r4, r2 + r5 + r4]]
        B = [v1, v2]

        # Hitung determinan
        det = A[0][0]*A[1][1] - A[0][1]*A[1][0]
        if det == 0:
            return None

        # Cramer's rule
        det_I1 = B[0]*A[1][1] - A[0][1]*B[1]
        det_I2 = A[0][0]*B[1] - B[0]*A[1][0]

        I1 = det_I1 / det
        I2 = det_I2 / det
        I3 = I1 - I2  # Arus cabang tengah

        return {'I1': I1, 'I2': I2, 'I3': I3}
    except Exception as e:
        return None
    
def parse_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/materi')
def materi():
    return render_template('materi.html')

@app.route('/contoh')
def contoh():
    return render_template('contoh.html')

@app.route("/kalkulator", methods=["GET", "POST"])
def kalkulator():
    total_capacitance = charge = energy = None
    voltage = configuration = None
    capacitors = []
    resistor_total = None
    resistors = []
    resistor_config = None
    tegangan = arus = hambatan = None
    ohm_result = False  # indikator apakah menampilkan hasil ohm

    if request.method == "POST":
        # Deteksi jenis perhitungan
        jenis = request.form.get("jenis")

        # Perhitungan Hukum Ohm
        if jenis == "ohm":
            V = request.form.get("tegangan", type=float)
            I = request.form.get("arus", type=float)
            R = request.form.get("hambatan", type=float)

            tegangan = V
            arus = I
            hambatan = R

            if V and I and not R:
                hambatan = V / I
            elif V and R and not I:
                arus = V / R
            elif I and R and not V:
                tegangan = I * R

            ohm_result = True
            print("V:", V, "I:", I, "R:", R)


        # Perhitungan Kapasitor
        configuration = request.form.get("configuration")
        capacitors = request.form.getlist("capacitor[]")
        capacitors = [float(c) for c in capacitors if c.strip() != '']
        voltage = request.form.get("voltage", type=float)

        if capacitors:
            if configuration == "seri":
                total_capacitance = 1 / sum(1 / c for c in capacitors)
            elif configuration == "paralel":
                total_capacitance = sum(capacitors)

            if voltage is not None and total_capacitance:
                charge = total_capacitance * voltage
                energy = 0.5 * total_capacitance * voltage**2

        # Perhitungan Resistor
        resistor_config = request.form.get("resistor_config")
        resistors = request.form.getlist("resistor[]")
        resistors = [float(r) for r in resistors if r.strip() != '']

        if resistors:
            if resistor_config == "seri":
                resistor_total = sum(resistors)
            elif resistor_config == "paralel":
                try:
                    resistor_total = 1 / sum(1 / r for r in resistors if r != 0)
                except ZeroDivisionError:
                    resistor_total = 0
                    

    jumlah_loop = request.form.get("jumlah_loop", "1")

    return render_template("kalkulator.html",
                           configuration=configuration,
                           capacitors=capacitors,
                           voltage=voltage,
                           total_capacitance=total_capacitance,
                           charge=charge,
                           energy=energy,
                           resistor_config=resistor_config,
                           resistors=resistors,
                           resistor_total=resistor_total,
                           ohm_result=ohm_result,
                           tegangan=tegangan,
                           arus=arus,
                           hambatan=hambatan,
                           jumlah_loop=jumlah_loop)
@app.route('/kirchhoff1', methods=['GET', 'POST'])
def kirchhoff1():
    result = None
    error = None
    v_total = None
    
    if request.method == 'POST':
        try:
            R1 = float(request.form.get('R1', '0').strip() or 0)
            R2 = float(request.form.get('R2', '0').strip() or 0)
            R3 = float(request.form.get('R3', '0').strip() or 0)

            v_str = request.form.get('Vtotal', '').strip()
            v_total = float(v_str) if v_str else 0.0

            total_R = R1 + R2 + R3
            if total_R == 0:
                raise ValueError("Jumlah resistansi tidak boleh nol.")

            I1 = (R1 / total_R) * v_total
            I2 = (R2 / total_R) * v_total
            I3 = (R3 / total_R) * v_total

            P1 = I1**2 * R1
            P2 = I2**2 * R2
            P3 = I3**2 * R3

            result = {
                'I1': round(I1, 4),
                'I2': round(I2, 4),
                'I3': round(I3, 4),
                'P1': round(P1, 4),
                'P2': round(P2, 4),
                'P3': round(P3, 4),
            }

        except Exception as e:
            result = {'error': f'Terjadi kesalahan: {str(e)}'}

    return render_template('kalkulator.html', result=result, v_total=v_total)




@app.route('/1loop', methods=['POST'])
def loop():
    try:
        resistors = []
        for i in range(1,6):
            val = request.form.get(f'r{i}')
            if val and val.strip() != '':
                resistors.append(float(val))
        V = float(request.form.get('v'))
        mode = request.form.get('mode')
        
        # Untuk sederhananya kita hitung resistansi total
        if mode == 'seri':
            R_total = sum(resistors)
        else:
            # paralel
            inv_sum = sum(1/r for r in resistors if r != 0)
            R_total = 1/inv_sum if inv_sum != 0 else 0
        
        if R_total == 0:
            current = 0
        else:
            current = V / R_total
        
        # Jika hanya 1 resistor dipakai, tampilkan current_1loop
        if len(resistors) == 1:
            return render_template('kalkulator.html', current_1loop=current)
        
        # Jika lebih, tampilkan currents I1, I2, I3 (dummy karena belum pakai loop 2)
        # Untuk saat ini, kita hanya tampilkan I1 = I2 = I3 = current agar tetap ada hasil
        currents = {'I1': current, 'I2': current, 'I3': current}
        return render_template('kalkulator.html', currents=currents)
    except Exception as e:
        return render_template('kalkulator.html', error=str(e))

@app.route('/kirchhoff2', methods=['POST', 'GET'])
def kirchhoff2():
    error = None
    currents_dict = None
    jumlah_loop = request.form.get("jumlah_loop") or request.args.get("jumlah_loop") or "1"

    if request.method == 'POST':
        try:
            if jumlah_loop == '2':
                loop1 = [parse_float(request.form.get(f"l1r{i}")) for i in range(1, 4)]
                loop2 = [parse_float(request.form.get(f"l2r{i}")) for i in range(1, 4)]
                v1 = parse_float(request.form.get("v1"))
                v2 = parse_float(request.form.get("v2"))
                dir1 = request.form.get("dir1", "searah")
                dir2 = request.form.get("dir2", "searah")
                loop_dir1 = request.form.get("loop_dir1", "searah")
                loop_dir2 = request.form.get("loop_dir2", "searah")

                import numpy as np

                try:
                    Rg1 = loop1[1] if loop1[1] is not None else 0
                    Rg2 = loop2[1] if loop2[1] is not None else 0
                    Rg = (Rg1 + Rg2) / 2 if (Rg1 and Rg2) else max(Rg1, Rg2)

                    A = np.array([
                        [ (loop1[0] or 0) + Rg + (loop1[2] or 0), -Rg],
                        [-Rg, (loop2[0] or 0) + Rg + (loop2[2] or 0)]
                    ])

                    b = np.array([v1 or 0, v2 or 0])
                    currents = np.linalg.solve(A, b)
                    I1, I2 = currents
                    currents_dict = {"I1": round(I1, 4), "I2": round(I2, 4), "I3": round(I1 - I2, 4)}
                except Exception as e:
                    error = f"Terjadi kesalahan perhitungan: {str(e)}"

                return render_template("kalkulator.html",
                                       jumlah_loop=jumlah_loop,
                                       loop1=loop1,
                                       loop2=loop2,
                                       v1=v1, v2=v2,
                                       dir1=dir1,
                                       dir2=dir2,
                                       loop_dir1=loop_dir1,
                                       loop_dir2=loop_dir2,
                                       currents=currents_dict,
                                       error=error)

            else:  # jumlah_loop == '1'
                R1 = parse_float(request.form.get("R1"))
                v1 = parse_float(request.form.get("v1"))
                dir1 = request.form.get("dir1", "searah")
                loop_dir1 = request.form.get("loop_dir1", "searah")

                try:
                    I1 = v1 / R1 if R1 and R1 != 0 else None
                    currents_dict = {"I1": round(I1, 4)} if I1 is not None else None
                except Exception as e:
                    error = f"Terjadi kesalahan perhitungan: {str(e)}"

                return render_template("kalkulator.html",
                                       jumlah_loop=jumlah_loop,
                                       R1=R1,
                                       v1=v1,
                                       dir1=dir1,
                                       loop_dir1=loop_dir1,
                                       currents=currents_dict,
                                       error=error)

        except Exception as e:
            error = f"Terjadi kesalahan saat perhitungan: {str(e)}"
            return render_template('kalkulator.html', error=error, jumlah_loop=jumlah_loop)

    # Jika method GET, render form default
    return render_template('kalkulator.html', jumlah_loop=jumlah_loop)

            
@app.route("/hukum_kirchhoff2", methods=["GET", "POST"])
def hukum_kirchhoff2():
    jumlah_loop = request.form.get("jumlah_loop", "1")
    return render_template("kalkulator.html", jumlah_loop=jumlah_loop)




if __name__ == '__main__':
    app.run(debug=True)
