#!/usr/bin/env python3
"""
Navi-LocalRAG - Agente desarrollador autónomo para local-rag.
Inicia sesión de trabajo y espera comandos del usuario.
"""

import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_PATH = '/home/iwakura/Documentos/github-projects/local-rag'
AGENT_PATH = f'{PROJECT_PATH}/agent'
LOG_DIR = f'{AGENT_PATH}/logs'
URGENCY_FILE = f'{AGENT_PATH}/urgency/pending.json'
APPROVAL_FILE = f'{AGENT_PATH}/approvals/pending.json'

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '7612282802')

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    import requests
    try:
        r = requests.post(url, json=data, timeout=10)
        return r.json().get('ok', False)
    except requests.RequestException:
        return False

def log_action(action, details):
    """Registra acción del agente."""
    os.makedirs(LOG_DIR, exist_ok=True)
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    log_file = f'{LOG_DIR}/{today}.log'
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a') as f:
        f.write(f'[{timestamp}] {action}: {details}\n')

def load_urgency():
    """Carga estado de urgencia."""
    if os.path.exists(URGENCY_FILE):
        with open(URGENCY_FILE) as f:
            return json.load(f)
    return {'messages': [], 'last_urgent': None}

def save_urgency(state):
    """Guarda estado de urgencia."""
    os.makedirs(f'{AGENT_PATH}/urgency', exist_ok=True)
    with open(URGENCY_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def check_urgency():
    """Verifica si hay mensajes sin responder que requieren urgencia."""
    state = load_urgency()
    if not state.get('messages'):
        return
    
    now = datetime.now(timezone.utc)
    for msg in state['messages']:
        sent_at_str = msg['sent_at'].replace('Z', '+00:00')
        sent_at = datetime.fromisoformat(sent_at_str)
        minutes_diff = (now - sent_at).total_seconds() / 60
        
        # Timeout base: 30 minutos
        if minutes_diff >= 30 and not msg.get('urgent'):
            msg['urgent'] = True
            msg['urgency_type'] = 'timeout'
            send_telegram(f'[URGENTE] No he tenido respuesta en 30 min.\nMensaje: {msg["content"][:200]}...\nOpciones:\na) Proceder\nb) Cancelar\nc) Modificar plan')
            log_action('URGENCY', f'Mensaje marcado urgente por timeout: {msg["id"]}')
        
        # Repeticiones: 3 veces
        if msg.get('repeat_count', 0) >= 3 and not msg.get('urgent'):
            msg['urgent'] = True
            msg['urgency_type'] = 'repetitions'
            send_telegram(f'[URGENTE] Mensaje enviado 3 veces sin respuesta.\nMensaje: {msg["content"][:200]}')
            log_action('URGENCY', f'Mensaje marcado urgente por repeticiones: {msg["id"]}')
    
    save_urgency(state)

def start_session():
    """Inicia nueva sesión de trabajo."""
    log_action('SESSION_START', f'Sesión iniciada a las {datetime.now(timezone.utc).strftime("%H:%M")}')
    
    session_file = f'{AGENT_PATH}/current_session.json'
    session = {
        'started_at': datetime.now(timezone.utc).isoformat(),
        'status': 'active',
        'tasks': [],
        'commits': []
    }
    
    with open(session_file, 'w') as f:
        json.dump(session, f, indent=2)
    
    return session

def end_session():
    """Termina sesión actual y genera resumen."""
    session_file = f'{AGENT_PATH}/current_session.json'
    if not os.path.exists(session_file):
        return
    
    with open(session_file) as f:
        session = json.load(f)
    
    session['ended_at'] = datetime.now(timezone.utc).isoformat()
    session['status'] = 'completed'
    
    # Generar resumen
    summary = f'''[SESIÓN TERMINADA] Navi-LocalRAG

Resumen de la sesión:
- Inicio: {session.get('started_at', 'N/A')}
- Fin: {session.get('ended_at', 'N/A')}
- Tareas completadas: {len(session.get('tasks', []))}
- Commits hechos: {len(session.get('commits', []))}

'''
    
    send_telegram(summary)
    log_action('SESSION_END', f'Sesión terminada, {len(session.get("tasks", []))} tareas')
    
    os.remove(session_file)

def add_pending_message(msg_id, content):
    """Agrega mensaje pendiente de respuesta."""
    state = load_urgency()
    state['messages'].append({
        'id': msg_id,
        'content': content,
        'sent_at': datetime.now(timezone.utc).isoformat(),
        'repeat_count': 0,
        'urgent': False
    })
    save_urgency(state)

def increment_repeat(msg_id):
    """Incrementa contador de repeticiones para un mensaje."""
    state = load_urgency()
    for msg in state['messages']:
        if msg['id'] == msg_id:
            msg['repeat_count'] = msg.get('repeat_count', 0) + 1
            save_urgency(state)
            return
    # Si no existe, crear uno nuevo
    add_pending_message(msg_id, f'Mensaje repetido #{msg_id}')

def remove_pending_message(msg_id):
    """Remueve mensaje pendiente (usuario respondió)."""
    state = load_urgency()
    state['messages'] = [m for m in state['messages'] if m['id'] != msg_id]
    save_urgency(state)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['start', 'stop', 'status', 'check-urgency'])
    args = parser.parse_args()
    
    if args.action == 'start':
        session = start_session()
        print(f'Sesión iniciada: {session["started_at"]}')
    elif args.action == 'stop':
        end_session()
        print('Sesión terminada')
    elif args.action == 'status':
        session_file = f'{AGENT_PATH}/current_session.json'
        if os.path.exists(session_file):
            with open(session_file) as f:
                print(json.dumps(json.load(f), indent=2))
        else:
            print('No hay sesión activa')
    elif args.action == 'check-urgency':
        check_urgency()
        print('Verificación de urgencia completada')