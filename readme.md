# Gestion de processus parallèles via bus de données

## Objectif

L'objectif de ce projet est de mettre en oeuvre les connaissances acquises en cours de programmation système sur la gestion de processus parallèles via bus de données.

## Fonctionnalités

```
$ python Launcher.py <nb_processus=3> <temps_execution=15> <verbose=00000000>
```

- `nb_processus` : nombre de processus à lancer
- `temps_execution` : temps d'exécution de chaque processus
- `verbose` : mode verbeux (affichage des messages de debug)

Le niveau de verbosité est donné sous la forme d'une chaîne de 0 et de 1, où chaque bit correspond à un type de verbosité.
`76543210`

- `0` : messages d'envoi réception de messages utilisateurs
- `1` : synchronisation
- `2` : acknowledgement
- `3` : section critique
- `4` : token
- `5` : heartbeats
- `6` : initialisation de l'id du processus
- `7` : actions du main

Fonctionnalités implémentées dans Com (voir `Com.py`) :
- [x] message entre 2 processus (`sendTo`)
- [x] message entre 2 processus synchrone (`sendToSync`, `recevFromSync`)
- [x] broadcast d'un message (`broadcast`)
- [x] broadcast d'un message synchrone (`broadcastSync`)
- [x] incrémentation de l'horloge logique (`inc_clock`)
- [x] synchronisation (`synchronize`)
- [x] section critique (`doCriticalAction`)
- [x] token (non accessible par l'utilisateur)
- [x] heartbeats (non accessible par l'utilisateur)
- [x] initialisation de l'id du processus (non accessible par l'utilisateur)

Le fichier `Process.py` contient la classe `Process` qui représente un processus. La fonction `run` ainsi que `criticalAction` sont modifiables par l'utilisateur.

## Implémentations

### Token

Le token tourne de processus en processus, en mode anneau.

### Heartbeats

Les heartbeats sont envoyés par chaque processus à tous les autres. Si un processus ne reçoit pas de heartbeat d'un autre processus, il le considère comme potentiellement mort. S'il ne reçoit pas de heartbeat d'un processus dans la liste des processus potentiellement morts, il le considère comme mort et met à jour son id. Si un processus reçoit un heartbeat d'un processus qu'il considérait comme mort, il le reconsidère comme vivant.

### Synchronisation

Lors de la synchronisation, le com passe en mode syncing. Quand le token arrive, le com update le nombre de processus en cours de synchronisation. Quand tous les processus sont en cours de synchronisation (nombre de synchronisation = 0), le com considère que tout le monde est synchronisé et continue son exécution.

### Section critique

Lorsqu'un processus veut entrer en section critique, il passe son TokenState à REQUESTED. Quand il reçoit le token, il passe son TokenState à SC ce qui lui permet d'entrer en section critique. Quand il sort de la section critique, il passe son TokenState à RELEASED et envoie le token au processus suivant avant de passer son TokenState à NULL.
Une fonction (`doCriticalAction`) se charge de gérer la section critique pour l'utilisateur et d'effectuer les requêtes et releases de celle-ci.

### Initialisation de l'id du processus

Lorsqu'un processus est créé, il envoie un message avec un nombre aléatoire grand à tous les autres processus. Chaque processus garde en mémoire les nombres aléatoires reçus. Quand un processus a reçu un nombre aléatoire de tous les autres processus, il vérifie s'il n'a pas reçu de doublons. Si c'est le cas, alors il recommence la procédure. Sinon, il trie la liste des nombres aléatoires reçus et prend comme id l'indice de la position de son nombre aléatoire dans la liste.

### Messages synchrones

Pour les messages synchrones, le processus qui envoie le message attend un acknowledgement de la part du processus qui reçoit le message. Pour le processus qui reçoit le message, il attend un message de la part du processus qui envoie le message. Quand il le reçoit, il envoie un acknowledgement au processus qui envoie le message et continue son exécution. Quand le processus qui envoie le message reçoit l'acknowledgement, il continue son exécution. Le broadcast synchrone utilise cette méthode pour envoyer un message à tous les processus.
