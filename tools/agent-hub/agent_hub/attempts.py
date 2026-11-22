"""Bind a new local coding session to a new task, a handoff or an independent review."""
import argparse
import json
import os
from pathlib import Path
import secrets
import tempfile

from .hooks import HookQueue, binding


def create_binding(profile, output, action, *, task_id=None, previous=None, artifact=None, attempt_id=None):
    if action not in {'start','handoff','verify'}:
        raise ValueError('invalid_action')
    if action != 'start' and not task_id:
        raise ValueError('task_id_required')
    if (action == 'handoff') != bool(previous):
        raise ValueError('specify_current_primary_for_handoff')
    if action == 'verify' and not artifact:
        raise ValueError('exact_artifact_required')
    # Keep credentials in the worker environment. Copy only the new host's declared configuration.
    fields = ('project','account','host','window','generation','tool','project_root','state_dir','endpoint',
              'wiki_dir','host_installation_id','terminal_session_id','journal_id','window_id','tool_version','session_id')
    config = {k:profile[k] for k in fields if k in profile}
    config.update(task_id=task_id or secrets.token_hex(16), attempt_id=attempt_id or secrets.token_hex(16),
                  role='verify' if action == 'verify' else 'primary')
    if previous:
        config['previous_attempt_id'] = previous
    if artifact:
        config['artifact'] = artifact
    config = binding(config)
    path = Path(output).absolute()
    root = Path(config['project_root'])
    if path.resolve().is_relative_to(root):
        raise ValueError('keep_binding_outside_project')
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as tmp:
        name = Path(tmp.name)
        try:
            json.dump(config,tmp,ensure_ascii=False,indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())
        except BaseException:
            tmp.close()
            name.unlink(missing_ok=True)
            raise
    try:
        os.link(name, path)  # Publish once; an existing execution binding is immutable.
    finally:
        name.unlink(missing_ok=True)
    return config


def announce(config):
    queue = HookQueue(config)
    # A stable manual step key makes a retry safe following a crash between binding and enqueue.
    return queue.enqueue({'step_id':'hub-execution-bound', 'status':'running',
                          'summary':'Registered this execution for ' + config['task_id'] + '.'}, manual=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['start','handoff','verify','resume-registration'])
    parser.add_argument('--binding',required=True,type=Path)
    parser.add_argument('--profile',type=Path)
    parser.add_argument('--task-id')
    parser.add_argument('--attempt-id')
    parser.add_argument('--previous-attempt')
    parser.add_argument('--artifact')
    args = parser.parse_args()
    try:
        if args.action == 'resume-registration':
            config = binding(json.loads(args.binding.read_text(encoding='utf-8-sig')))
        else:
            if not args.profile:
                parser.error('--profile is required for a new local execution')
            profile = json.loads(args.profile.read_text(encoding='utf-8-sig'))
            config = create_binding(profile, args.binding, args.action, task_id=args.task_id, previous=args.previous_attempt,
                                    artifact=args.artifact, attempt_id=args.attempt_id)
        eid = announce(config)
    except (ValueError,OSError,KeyError,RuntimeError) as exc:
        parser.exit(1, f'Registration failed ({type(exc).__name__}); check binding, private directory and queue.\n')
    print(json.dumps({'project':config['project'],'task_id':config['task_id'],'attempt_id':config['attempt_id'],
                      'event_id':eid,'state':'queued_locally'}))


if __name__ == '__main__':
    main()
