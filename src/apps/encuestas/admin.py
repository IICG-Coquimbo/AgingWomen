"""Los modelos de encuestas NO se registran en el Django Admin a propósito.

Los datos clínicos de las participantes (Identificación, MRS, EMPA, hábitos,
etc.) solo se consultan desde el panel profesional (/profesional/), que exige
rol PROFESIONAL. El Django Admin queda solo para la gestión de cuentas
(apps.usuarios).
"""
