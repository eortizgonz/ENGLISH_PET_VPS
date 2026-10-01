"""Start local PET Quest with Gmail credentials held only in process memory."""
import getpass
import os
import re


def main():
    email = input('Correo Gmail remitente: ').strip().lower()
    if not re.fullmatch(r'[^\s@]+@gmail\.com', email):
        raise SystemExit('Introduce una cuenta @gmail.com.')
    password = ''.join(getpass.getpass('Contraseña de aplicación (oculta): ').split())
    if not re.fullmatch(r'[a-zA-Z]{16}', password):
        raise SystemExit('La contraseña de aplicación debe tener 16 letras.')
    os.environ.update({
        'PETQUEST_SMTP_HOST': 'smtp.gmail.com',
        'PETQUEST_SMTP_PORT': '587',
        'PETQUEST_SMTP_TLS': '1',
        'PETQUEST_SMTP_USER': email,
        'PETQUEST_SMTP_FROM': email,
        'PETQUEST_SMTP_PASSWORD': password,
        'PETQUEST_DEV_MODE': '0',
    })
    print('Credenciales listas para esta ejecución. No se guardarán en archivos.')
    # Import only after setting SMTP variables: api_server reads them at import.
    # Use exactly the regular server entry point, without a second launcher.
    import api_server
    print(f'Abre http://{api_server.HOST}:{api_server.PORT} en tu navegador.', flush=True)
    try:
        return api_server.main()
    except KeyboardInterrupt:
        print('\nServidor detenido.')
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
