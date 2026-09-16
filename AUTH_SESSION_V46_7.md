# PET Quest V46.7 - Inicio y cierre de sesion

Implementado:
- Login obligatorio para acceder a contenido protegido.
- Restauracion automatica de sesion mediante token persistente.
- Expiracion local de sesion y revalidacion contra `/api/me`.
- Cierre de sesion global visible en la barra superior.
- Logout invalida la sesion en backend y limpia tokens locales.
- Respuestas 401 de endpoints protegidos regresan automaticamente al login.
- Enter en el campo contrasena ejecuta el login.
- Las credenciales demo solo aparecen en development/test, como antes.

Version: 46.7
