# LAPP – Plataforma Multiherramienta Operativa

LAPP es una **aplicación web multiherramienta** desarrollada para centralizar, automatizar y simplificar procesos operativos críticos dentro de entornos industriales y corporativos. Su objetivo principal es **reducir la dependencia del área IT para tareas repetitivas**, otorgando autonomía a personal no técnico, manteniendo control, trazabilidad y seguridad.

---

## 🧩 Problema que resuelve

En entornos operativos complejos suelen coexistir:

* Personal no técnico sin acceso a herramientas críticas de red.
* Sobrecarga del departamento IT con tareas manuales y repetitivas.
* Procesos dispersos en múltiples sistemas y documentos.
* Falta de control centralizado de recursos, personal y equipos.
* Alto riesgo operativo ante emergencias.

**LAPP unifica todos estos procesos en una sola plataforma**, accesible, segura y orientada a la operación diaria.

---

## 🎯 Objetivos de la plataforma

* Centralizar herramientas operativas en un único sistema.
* Automatizar tareas críticas de red e infraestructura.
* Mejorar la trazabilidad de recursos, equipos y personal.
* Reducir errores humanos y tiempos de ejecución.
* Proveer interfaces simples para usuarios no técnicos.

---

## 🛠️ Tecnologías utilizadas

### Backend

* **Python**
* **Django** (framework principal)
* **Django Auth** (gestión de usuarios, grupos y permisos)
* **Scripts Python** para automatización de red

### Frontend

* **HTML5 / CSS3**
* **Bootstrap** (layout, iconografía y responsividad)
* **JavaScript**
* **SweetAlert2** (notificaciones interactivas)

### Integraciones externas

* **Slack API** (notificaciones automáticas)
* **WhatsApp** (envío manual de resúmenes operativos)
* **SharePoint** (sincronización de archivos)
* **rclone** (sincronización cloud)
* **Binance Widget** (información cripto)

### Infraestructura

* Linux
* Cron jobs
* Rclone

---

## 🔐 Autenticación y Home

### Login

* Autenticación flexible mediante **email o username**.
* Validaciones robustas con mensajes personalizados.
* Redirección automática tras login exitoso.
* Notificación de bienvenida con SweetAlert2.

### Dashboard Home

* Layout modular basado en *cards*.
* Código de colores por tipo de herramienta:

  * Scripts
  * Formularios
  * Guardias
  * Utilidades
* Accesos rápidos a plataformas corporativas.
* Widgets informativos:

  * Cotización del dólar
  * Criptomonedas (Binance)
  * Timestamp actualizado

---

## 🧰 TOOLS – Scripts de Red

### SWCore – Control de VLANs (Core)

* Gestión centralizada de VLANs a nivel **switch core**.
* Acciones masivas: `shutdown / no shutdown` por grupos.
* Configuración persistente (sobrevive a reinicios).
* Ideal para emergencias eléctricas o mantenimientos mayores.

### SWD / SWA – Control de Interfaces

* Control directo de puertos físicos.
* Cambios inmediatos en conectividad.
* Uso puntual para mantenimiento.
* Separación lógica:

  * **SWD**: switches de distribución.
  * **SWA**: switches de acceso.

---

## 🧪 TOOLS – Diagnóstico y Estado

### CDP Neighbors

* Ejecución del comando `show cdp neighbors`.
* Escaneo por rangos de IP.
* Mapeo completo SWA → SWD.
* Validación de orden de puertos estándar (Fa0/47 y Fa0/48).
* Control de topología y estandarización.

### Interface Status

* Monitoreo de enlaces troncales hacia el Core.
* Comando ejecutado:

  ```bash
  show interface status | i Gi1/1/|Gi2/1/
  ```
* Verificación de fibras SFP.
* Control de stacking (2 fibras por switch).

---

## 📝 FORMS – Plataforma Elevadora

### Checklist Operativo

* Inspección pre-operativa guiada.
* Preguntas críticas de seguridad.

### Detección de NOK

* Identificación automática de respuestas negativas.
* Disparo de acciones inmediatas.

### Notificación por Slack

* Envío automático al canal `#notifi_lapp`.
* Incluye:

  * Usuario
  * Equipo
  * Fecha y hora
  * Ubicación
  * Preguntas NOK

### Gestión del Estado

* Equipos marcados automáticamente como **fuera de servicio**.
* Prevención de uso inseguro.

### Trazabilidad

* Historial completo de uso.
* Última falla registrada.
* Responsable identificado.

---

## 🏗️ FORMS – Estado de Infraestructura

### Inspección Visual

* Control de:

  * Extractores (8x8)
  * Bombas (4x4)
  * Transformadores (1x8)
* 5 Warehouses
* 8 módulos por warehouse

### Persistencia en Sesión

* Los datos se guardan en sesión.
* Permite inspecciones no lineales.

### Reporte Excel

* Generación automática de `.xlsx`.
* Incluye:

  * Usuario
  * Fecha y hora
  * Resultados completos
* Archivo listo para métricas y Power BI.

### Sincronización SharePoint

* Cron job ejecuta script con rclone.
* Ruta destino:

  ```
  BITF Paraguay/Documentos/10 - Mantenimiento/06 - Registros/Checklists/
  ```

---

## ⏱️ Horas Extras y Guardias

### Guardias

* Asignación programada por administradores.
* Fechas de inicio y fin automáticas (16:00 → 07:00).
* Validaciones frontend (no fechas pasadas).
* Visualización pública de guardias.
* Control de acceso por grupos (`admin_group`).

### Horas Extras

#### Registro de Usuario

* Carga individual de horas.
* Selección de ponderación: 50% o 100%.
* Historial personal visible.

#### Gestión Administrativa

* Aprobación o rechazo.
* Feedback obligatorio.
* Filtros por área (OPS, MTO, IT).
* Importación automática de guardias (últimos 40 días al 25%).

#### Estadísticas

* Totales por:

  * Usuario
  * Mes
  * Porcentaje
* Tablas listas para análisis.

---

## 🍽️ RuralApp – Menú Diario

### Menú Dinámico

* Dos platos principales diarios.
* Ciclo automático de 4 semanas.
* 15 ensaladas fijas.
* Opción de guarnición.

### Ventana Horaria

* Pedidos habilitados de **08:30 a 13:09**.
* Bloqueo automático fuera de horario.
* Visualización del menú del día siguiente.

### Resumen para Catering

* Consolidación automática de pedidos.
* Agrupación por plato y cantidad.
* Comentarios incluidos.

### Envío por WhatsApp

* Formato listo para copiar/pegar.
* Optimizado para comunicación rápida.

### Experiencia de Usuario

* Confirmaciones visuales y sonoras.
* SweetAlert2 con GIF y sonido.
* Tabla compartida con órdenes recientes.

---

## 📌 Estado del proyecto

LAPP es un proyecto **en uso real**, en constante evolución, diseñado para adaptarse a nuevas necesidades operativas.

---

## 👤 Autor

Desarrollado íntegramente por **Yúber Millán**.

* Python / Django
* Automatización de infraestructura
* Operación IT / OT

---

## 📄 Licencia

Uso interno / corporativo. Adaptable según necesidad.
