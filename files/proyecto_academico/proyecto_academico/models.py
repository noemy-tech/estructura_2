from datetime import date


# =====================================================================
# CLASE BASE: lo que los tres modelos comparten  (NO SE TOCA)
# =====================================================================
class ModeloBase:
    """Padre de todos los modelos. Guarda el id y define el comportamiento común."""

    def __init__(self, id_registro):
        self.id = int(id_registro)

    # ---- ÚNICO MÉTODO DE CLASE DEL PROYECTO ----
    @classmethod
    def desde_diccionario(cls, datos):
        """Diccionario -> objeto. Escrito UNA vez y usado por los tres modelos.
        cls es la clase que llamó: Estudiante, Materia o Matricula."""
        datos = dict(datos)                 # copia, para no tocar el original
        id_registro = datos.pop("id")       # saco el id
        return cls(id_registro, **datos)    # el resto son los campos del modelo

    # ---- MÉTODOS DE INSTANCIA ----
    def a_diccionario(self):
        return {"id": self.id}

    def etiqueta(self):
        # POLIMORFISMO: cada hijo la reescribe a su manera
        return f"registro {self.id}"

    def __str__(self):
        return f"[{self.id}] {self.etiqueta()}"


# =====================================================================
# PERSONA (se reutiliza tal cual)
# =====================================================================
class Persona(ModeloBase):
    """Todo lo que tiene una persona del sistema."""

    def __init__(self, id_registro, nombre, apellido, email):
        super().__init__(id_registro)
        self.nombre = nombre
        self.apellido = apellido
        self.email = email

    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def a_diccionario(self):
        datos = super().a_diccionario()
        datos["nombre"] = self.nombre
        datos["apellido"] = self.apellido
        datos["email"] = self.email
        return datos

    def etiqueta(self):
        return self.nombre_completo()


# =====================================================================
# ESTUDIANTE  (equivale a Cliente)
# =====================================================================
class Estudiante(Persona):
    """Estudiante ES UNA Persona, con carnet y carrera."""

    def __init__(self, id_registro, nombre, apellido, email, carnet="", carrera=""):
        super().__init__(id_registro, nombre, apellido, email)
        self.carnet = carnet
        self.carrera = carrera

    def a_diccionario(self):
        datos = super().a_diccionario()      # id + nombre + apellido + email
        datos["carnet"] = self.carnet
        datos["carrera"] = self.carrera
        return datos

    def etiqueta(self):
        # Sobrescribe y EXTIENDE la del padre
        return f"{super().etiqueta()} · {self.carnet} · {self.carrera or 'sin carrera'}"


# =====================================================================
# MATERIA  (equivale a Producto): aquí vive TODO lo estático
# =====================================================================
class Materia(ModeloBase):
    """Materia ES UN ModeloBase. Los cupos hacen el papel del stock."""

    # ATRIBUTOS ESTÁTICOS (de clase): existen una sola vez, no por objeto
    CUPOS_MAXIMOS = 30
    NOTA_APROBACION = 14

    def __init__(self, id_registro, nombre, codigo, creditos=0, cupos=0):
        super().__init__(id_registro)
        self.nombre = nombre
        self.codigo = codigo
        self.creditos = int(creditos)
        self.cupos = int(cupos)

    # MÉTODO ESTÁTICO: no usa self ni cls
    @staticmethod
    def es_nota_valida(valor):
        try:
            return 0 <= float(valor) <= 20
        except (TypeError, ValueError):
            return False

    # MÉTODOS DE INSTANCIA
    def hay_cupo(self):
        return self.cupos > 0

    def ocupar_cupo(self):
        self.cupos -= 1

    def liberar_cupo(self):
        self.cupos += 1

    def a_diccionario(self):
        datos = super().a_diccionario()
        datos["nombre"] = self.nombre
        datos["codigo"] = self.codigo
        datos["creditos"] = self.creditos
        datos["cupos"] = self.cupos
        return datos

    def etiqueta(self):
        alerta = "" if self.hay_cupo() else " ⚠ sin cupo"
        return (f"{self.codigo} · {self.nombre} · {self.creditos} créditos · "
                f"cupos {self.cupos}{alerta}")


# =====================================================================
# MATRÍCULA  (equivale a Venta): une estudiante y materia por id
# =====================================================================
class Matricula(ModeloBase):
    """Una matrícula: un estudiante, una materia, un periodo y (luego) una nota."""

    def __init__(self, id_registro, estudiante_id, materia_id, periodo,
                 nota=None, fecha=""):
        super().__init__(id_registro)
        self.estudiante_id = int(estudiante_id)
        self.materia_id = int(materia_id)
        self.periodo = periodo
        # None significa "todavía sin calificar" (se guarda como null en el JSON)
        self.nota = None if nota in (None, "") else float(nota)
        self.fecha = fecha or date.today().isoformat()

    def esta_aprobada(self):
        return self.nota is not None and self.nota >= Materia.NOTA_APROBACION

    def estado(self):
        # Se calcula, NO se guarda: nunca queda desactualizado
        if self.nota is None:
            return "Sin calificar"
        return "Aprobado" if self.esta_aprobada() else "Reprobado"

    def a_diccionario(self):
        datos = super().a_diccionario()
        datos["estudiante_id"] = self.estudiante_id
        datos["materia_id"] = self.materia_id
        datos["periodo"] = self.periodo
        datos["nota"] = self.nota
        datos["fecha"] = self.fecha
        return datos

    def etiqueta(self):
        nota = "-" if self.nota is None else f"{self.nota:.1f}"
        return (f"{self.periodo} · estudiante {self.estudiante_id} · "
                f"materia {self.materia_id} · nota {nota} ({self.estado()})")
