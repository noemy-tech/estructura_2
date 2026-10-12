from abc import ABC, abstractmethod

from models import Estudiante, Materia, Matricula
from shared.json_manager import GestorJSON
from shared.herramientas import es_email_valido


def _entero_en_rango(valor, minimo, maximo):
    """True si 'valor' es un entero (en texto o número) entre minimo y maximo."""
    texto = str(valor).strip()
    return texto.isdigit() and minimo <= int(texto) <= maximo


# =====================================================================
# CLASE BASE (ABSTRACTA): lista de compromisos de todo controlador
# =====================================================================
class CrudBase(ABC):
    @abstractmethod
    def leer(self):
        pass

    @abstractmethod
    def obtener(self, id_registro):
        pass

    @abstractmethod
    def buscar(self, texto):
        pass

    @abstractmethod
    def siguiente(self):
        pass

    @abstractmethod
    def crear(self, datos):
        pass

    @abstractmethod
    def actualizar(self, id_registro, datos):
        pass

    @abstractmethod
    def eliminar(self, id_registro):
        pass


# =====================================================================
# CONTROLADOR DE ESTUDIANTES
# =====================================================================
class EstudianteController(CrudBase):
    # TUPLA: campos donde se busca. Es fija, por eso no es lista.
    CAMPOS_BUSCABLES = ("nombre", "apellido", "email", "carnet", "carrera")
    # CONJUNTO: campos permitidos al actualizar (sirve para la diferencia de conjuntos)
    CAMPOS_EDITABLES = {"nombre", "apellido", "email", "carnet", "carrera"}

    def __init__(self, archivo="data/estudiantes.json"):
        self.gestor = GestorJSON(archivo)
        # LISTA de objetos Estudiante construidos desde los diccionarios del JSON
        self.lista = []
        for datos in self.gestor.leer():
            self.lista.append(Estudiante.desde_diccionario(datos))

    def guardar(self):
        datos = []
        for estudiante in self.lista:
            datos.append(estudiante.a_diccionario())
        self.gestor.guardar(datos)

    def validar(self, datos, id_actual=None):
        """Devuelve un mensaje de error, o None si todo está bien."""
        # Obligatorios: solo al crear. Al actualizar basta con lo que cambia.
        if id_actual is None:
            for campo in ("nombre", "apellido", "email", "carnet"):
                if str(datos.get(campo, "")).strip() == "":
                    return f"El campo {campo} es obligatorio"

        if "email" in datos:
            email = str(datos["email"]).strip().lower()
            if not es_email_valido(email):
                return f"Email inválido: '{email}'"
            # CONJUNTO: emails de los OTROS estudiantes. 'in' es instantáneo.
            emails_usados = {e.email for e in self.lista if e.id != id_actual}
            if email in emails_usados:
                return "Ese email ya está registrado"

        if "carnet" in datos:
            carnet = str(datos["carnet"]).strip().upper()
            if carnet == "":
                return "El carnet no puede quedar vacío"
            # CONJUNTO: carnets de los OTROS estudiantes (sin repetidos, búsqueda rápida)
            carnets_usados = {e.carnet.upper() for e in self.lista if e.id != id_actual}
            if carnet in carnets_usados:
                return "Ese carnet ya está registrado"
        return None

    def leer(self):
        return self.lista

    def obtener(self, id_estudiante):
        for estudiante in self.lista:
            if estudiante.id == id_estudiante:
                return estudiante
        return None

    def buscar(self, texto):
        texto = texto.strip().lower()
        encontrados = []
        if texto == "":
            return encontrados
        for estudiante in self.lista:
            for campo in self.CAMPOS_BUSCABLES:
                if texto in str(getattr(estudiante, campo)).lower():
                    encontrados.append(estudiante)
                    break               # ya coincidió: no lo agregamos dos veces
        return encontrados

    def siguiente(self):
        mayor = 0
        for estudiante in self.lista:
            if estudiante.id > mayor:
                mayor = estudiante.id
        return mayor + 1

    def crear(self, datos):
        error = self.validar(datos)
        if error:
            return False, error
        estudiante = Estudiante(self.siguiente(),
                                str(datos["nombre"]).strip().title(),
                                str(datos["apellido"]).strip().title(),
                                str(datos["email"]).strip().lower(),
                                str(datos["carnet"]).strip().upper(),
                                str(datos.get("carrera", "")).strip().title())
        self.lista.append(estudiante)
        self.guardar()
        return True, f"Estudiante creado: {estudiante.etiqueta()}"

    def actualizar(self, id_estudiante, datos):
        estudiante = self.obtener(id_estudiante)
        if estudiante is None:
            return False, f"No existe un estudiante con id {id_estudiante}"
        if not datos:
            return False, "No se indicó ningún cambio"
        # DIFERENCIA de conjuntos: campos que no existen en un estudiante
        desconocidos = set(datos) - self.CAMPOS_EDITABLES
        if desconocidos:
            return False, f"Campos no válidos: {', '.join(sorted(desconocidos))}"
        # Se valida ANTES de tocar el objeto: si algo falla, no cambia nada
        error = self.validar(datos, id_estudiante)
        if error:
            return False, error
        for campo, valor in datos.items():
            valor = str(valor).strip()
            if campo in ("nombre", "apellido", "carrera"):
                valor = valor.title()
            elif campo == "email":
                valor = valor.lower()
            elif campo == "carnet":
                valor = valor.upper()
            setattr(estudiante, campo, valor)
        self.guardar()
        return True, f"Estudiante {id_estudiante} actualizado"

    def eliminar(self, id_estudiante):
        estudiante = self.obtener(id_estudiante)
        if estudiante is None:
            return False, f"No existe un estudiante con id {id_estudiante}"
        self.lista.remove(estudiante)
        self.guardar()
        return True, f"Estudiante {id_estudiante} eliminado"

    # --- propio de estudiantes ---
    def carreras(self):
        """CONJUNTO de carreras: sin repetidos. sorted() lo devuelve como lista."""
        return sorted({e.carrera for e in self.lista if e.carrera != ""})


# =====================================================================
# CONTROLADOR DE MATERIAS
# =====================================================================
class MateriaController(CrudBase):
    CAMPOS_EDITABLES = {"nombre", "codigo", "creditos", "cupos"}

    def __init__(self, archivo="data/materias.json"):
        self.gestor = GestorJSON(archivo)
        self.lista = []
        for datos in self.gestor.leer():
            self.lista.append(Materia.desde_diccionario(datos))

    def guardar(self):
        datos = []
        for materia in self.lista:
            datos.append(materia.a_diccionario())
        self.gestor.guardar(datos)

    def validar(self, datos, id_actual=None):
        if id_actual is None:
            for campo in ("nombre", "codigo", "creditos"):
                if str(datos.get(campo, "")).strip() == "":
                    return f"El campo {campo} es obligatorio"

        if "codigo" in datos:
            codigo = str(datos["codigo"]).strip().upper()
            if codigo == "":
                return "El código no puede quedar vacío"
            # CONJUNTO de códigos de las OTRAS materias
            codigos_usados = {m.codigo.upper() for m in self.lista if m.id != id_actual}
            if codigo in codigos_usados:
                return f"Ya existe una materia con el código {codigo}"

        if "creditos" in datos and not _entero_en_rango(datos["creditos"], 1, 10):
            return "Los créditos deben ser un entero entre 1 y 10"

        cupos = str(datos.get("cupos", "")).strip()
        if cupos != "" and not _entero_en_rango(cupos, 0, Materia.CUPOS_MAXIMOS):
            return f"Los cupos deben ser un entero entre 0 y {Materia.CUPOS_MAXIMOS}"
        return None

    def leer(self):
        return self.lista

    def obtener(self, id_materia):
        for materia in self.lista:
            if materia.id == id_materia:
                return materia
        return None

    def buscar(self, texto):
        texto = texto.strip().lower()
        encontradas = []
        if texto == "":
            return encontradas
        for materia in self.lista:
            if texto in materia.nombre.lower() or texto in materia.codigo.lower():
                encontradas.append(materia)
        return encontradas

    def siguiente(self):
        mayor = 0
        for materia in self.lista:
            if materia.id > mayor:
                mayor = materia.id
        return mayor + 1

    def crear(self, datos):
        error = self.validar(datos)
        if error:
            return False, error
        # Si no escriben los cupos, la materia abre con el máximo
        cupos = str(datos.get("cupos", "")).strip()
        materia = Materia(self.siguiente(),
                          str(datos["nombre"]).strip().title(),
                          str(datos["codigo"]).strip().upper(),
                          int(datos["creditos"]),
                          int(cupos) if cupos != "" else Materia.CUPOS_MAXIMOS)
        self.lista.append(materia)
        self.guardar()
        return True, f"Materia creada: {materia.etiqueta()}"

    def actualizar(self, id_materia, datos):
        materia = self.obtener(id_materia)
        if materia is None:
            return False, f"No existe una materia con id {id_materia}"
        if not datos:
            return False, "No se indicó ningún cambio"
        desconocidos = set(datos) - self.CAMPOS_EDITABLES
        if desconocidos:
            return False, f"Campos no válidos: {', '.join(sorted(desconocidos))}"
        error = self.validar(datos, id_materia)
        if error:
            return False, error
        if "nombre" in datos:
            materia.nombre = str(datos["nombre"]).strip().title()
        if "codigo" in datos:
            materia.codigo = str(datos["codigo"]).strip().upper()
        if "creditos" in datos:
            materia.creditos = int(datos["creditos"])
        if "cupos" in datos:
            materia.cupos = int(datos["cupos"])
        self.guardar()
        return True, f"Materia {id_materia} actualizada"

    def eliminar(self, id_materia):
        materia = self.obtener(id_materia)
        if materia is None:
            return False, f"No existe una materia con id {id_materia}"
        self.lista.remove(materia)
        self.guardar()
        return True, f"Materia {id_materia} eliminada"

    # --- propio de materias ---
    def materias_sin_cupo(self):
        sin_cupo = []
        for materia in self.lista:
            if not materia.hay_cupo():
                sin_cupo.append(materia)
        return sin_cupo


# =====================================================================
# CONTROLADOR DE MATRÍCULAS
# =====================================================================
class MatriculaController(CrudBase):
    def __init__(self, estudiantes, materias, archivo="data/matriculas.json"):
        # La matrícula USA a los otros dos controladores.
        # Hay que pasarle los MISMOS que usa main.py.
        self.estudiantes = estudiantes
        self.materias = materias
        self.gestor = GestorJSON(archivo)
        self.lista = []
        for datos in self.gestor.leer():
            self.lista.append(Matricula.desde_diccionario(datos))

    def guardar(self):
        datos = []
        for matricula in self.lista:
            datos.append(matricula.a_diccionario())
        self.gestor.guardar(datos)

    def validar(self, datos):
        try:
            estudiante_id = int(datos.get("estudiante_id", 0))
            materia_id = int(datos.get("materia_id", 0))
        except (TypeError, ValueError):
            return "estudiante_id y materia_id deben ser números enteros"

        periodo = str(datos.get("periodo", "")).strip()
        if periodo == "":
            return "El periodo es obligatorio (ejemplo: 2026-1)"

        # CONJUNTO de ids existentes: preguntar 'x in conjunto' es instantáneo
        ids_estudiantes = {e.id for e in self.estudiantes.leer()}
        if estudiante_id not in ids_estudiantes:
            return f"No existe un estudiante con id {estudiante_id}"

        materia = self.materias.obtener(materia_id)
        if materia is None:
            return f"No existe una materia con id {materia_id}"

        # CONJUNTO de TUPLAS (estudiante, materia, periodo): se comparan los tres JUNTOS.
        # Una tupla puede estar dentro de un set; una lista no.
        ya_matriculados = {(m.estudiante_id, m.materia_id, m.periodo) for m in self.lista}
        if (estudiante_id, materia_id, periodo) in ya_matriculados:
            return "Ese estudiante ya está matriculado en esa materia en ese periodo"

        if not materia.hay_cupo():
            return f"No hay cupos disponibles en {materia.nombre}"
        return None

    def leer(self):
        return self.lista

    def obtener(self, id_matricula):
        for matricula in self.lista:
            if matricula.id == id_matricula:
                return matricula
        return None

    def buscar(self, texto):
        # Las matrículas se buscan por periodo, ej: "2026-1"
        texto = texto.strip()
        encontradas = []
        if texto == "":
            return encontradas
        for matricula in self.lista:
            if texto in matricula.periodo:
                encontradas.append(matricula)
        return encontradas

    def siguiente(self):
        mayor = 0
        for matricula in self.lista:
            if matricula.id > mayor:
                mayor = matricula.id
        return mayor + 1

    def crear(self, datos):
        # datos = {"estudiante_id": 1, "materia_id": 2, "periodo": "2026-1"}
        error = self.validar(datos)
        if error:
            return False, error
        materia = self.materias.obtener(int(datos["materia_id"]))
        matricula = Matricula(self.siguiente(),
                              int(datos["estudiante_id"]),
                              materia.id,
                              str(datos["periodo"]).strip())
        materia.ocupar_cupo()
        self.materias.guardar()          # guarda el cupo nuevo en materias.json
        self.lista.append(matricula)
        self.guardar()                   # guarda la matrícula en matriculas.json
        return True, f"Matrícula {matricula.id} registrada ({materia.nombre}, {matricula.periodo})"

    def registrar_nota(self, id_matricula, nota):
        matricula = self.obtener(id_matricula)
        if matricula is None:
            return False, f"No existe la matrícula {id_matricula}"
        # es_nota_valida es el método ESTÁTICO de Materia
        if not Materia.es_nota_valida(nota):
            return False, f"Nota inválida: '{nota}' (debe ser un número entre 0 y 20)"
        matricula.nota = float(nota)
        self.guardar()
        return True, f"Nota {matricula.nota:.1f} registrada: {matricula.estado()}"

    def actualizar(self, id_matricula, datos):
        # En una matrícula lo único que cambia es la nota
        if set(datos) != {"nota"}:
            return False, "Solo se puede modificar la nota de una matrícula"
        return self.registrar_nota(id_matricula, datos["nota"])

    def eliminar(self, id_matricula):
        """Retirar una matrícula: se borra y el cupo vuelve a la materia."""
        matricula = self.obtener(id_matricula)
        if matricula is None:
            return False, f"No existe la matrícula {id_matricula}"
        materia = self.materias.obtener(matricula.materia_id)
        if materia is not None:
            materia.liberar_cupo()
            self.materias.guardar()
        self.lista.remove(matricula)
        self.guardar()
        return True, f"Matrícula {id_matricula} retirada y cupo devuelto"

    def retirar_matricula(self, id_matricula):
        return self.eliminar(id_matricula)

    # --- propio de matrículas ---
    def certificado(self, id_matricula):
        matricula = self.obtener(id_matricula)
        if matricula is None:
            return None
        # DICCIONARIOS ÍNDICE {id: objeto}: acceso directo por id, sin recorrer listas
        estudiantes = {e.id: e for e in self.estudiantes.leer()}
        materias = {m.id: m for m in self.materias.leer()}
        estudiante = estudiantes.get(matricula.estudiante_id)
        materia = materias.get(matricula.materia_id)

        nombre = estudiante.nombre_completo() if estudiante else "eliminado"
        carnet = estudiante.carnet if estudiante else "-"
        nota = "sin registrar" if matricula.nota is None else f"{matricula.nota:.1f}"
        texto = f"CERTIFICADO #{matricula.id}   periodo: {matricula.periodo}\n"
        texto += f"Estudiante: {nombre}   ({carnet})\n"
        if materia:
            texto += f"Materia   : {materia.nombre}   ({materia.codigo}) · {materia.creditos} créditos\n"
        else:
            texto += "Materia   : eliminada\n"
        texto += "-" * 42 + "\n"
        texto += f"Nota      : {nota}\n"
        texto += f"Estado    : {matricula.estado()}"
        return texto

    def matriculas_por_estudiante(self):
        """DICCIONARIO de LISTAS: {estudiante_id: [matrículas de ese estudiante]}."""
        agrupadas = {}
        for matricula in self.lista:
            # setdefault: si el estudiante no estaba, crea la lista vacía y luego agrega
            agrupadas.setdefault(matricula.estudiante_id, []).append(matricula)
        return agrupadas

    def promedio_de_estudiante(self, id_estudiante):
        """Promedio de las notas ya registradas, o None si todavía no tiene ninguna."""
        notas = []
        for matricula in self.matriculas_por_estudiante().get(id_estudiante, []):
            if matricula.nota is not None:
                notas.append(matricula.nota)
        if not notas:
            return None
        return round(sum(notas) / len(notas), 2)

    def total_aprobadas(self):
        total = 0
        for matricula in self.lista:
            if matricula.esta_aprobada():
                total += 1
        return total
