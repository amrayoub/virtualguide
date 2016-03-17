# Virtual Guide

Virtual Guide é um projeto com o intuito de ser um aplicativo único para as mais diversas exposições.
A idéia central é utilizar um aplicativo único para qualquer exposição, seja algo pequeno como um garage sale com algumas dezenas de peças até um grande museu com centenas de obras.

### Você precisará de:
- Servidor REST que está no diretório VirtualRestServer com o nome virtrest.py
- Interface de administração que está em VirtualRest com o nome adminvirt.py
- Uma base de dados MongoDB
- Satisfazer as dependências:
 - Python 2.7
 - M2Crypto
 - Flask
 - PyMongo
 - ColorThief
 - PyQRCode

### Como ele funciona

É relativamente simples, o sistema é divido em 4 partes:
 1) O cliente mobile
 2) O Servidor REST
 3) O Banco de Dados
 4) A interface de administração

Client <--> REST <--> MongoDB <--> Admin Interface
                 \              /
                  --> GridFS <--

1) O administrador insere os dados no banco de dados
2) O cliente faz requisições ao servidor REST
3) O servidor REST valida as requisições, consulta o banco de dados e devolve uma resposta.

### FAQ
Por que utilizar um banco NoSQL?
Performance, simples assim. As bases não precisam de relacionamentos nem de constraints, são simples repositórios. Portanto, são casos típicos de uso de bases NoSQL.

Por que usar GridFS?
Quando imaginei este aplicativo, pensei no Museu do Louvre, com milhares de obras e uma infinidade de usuário o tempo todo!
O MongoDB e GridFS foram feitos com a idea de Cluster. Crescimento horizontal. Caso seja necessário utilizar vários servidores, distribuir os arquivos em diversos servidores seria um problema. Replicação, rsync, GFS, OCFS, storage externo... Isso dificulta e encarece uma solução simples. Com o MongoDB e GridFS, basta adicionar servidores com discos internos e pronto. Simples, rápido, barato e muito mais eficiente. Para quê complicar? Keep It Simple - KIS right? :)

### Ele está pronto?
Nãaaaao! De forma alguma. Ele está usável!
Fiz todas estas peças de software em 3 semanas! Muitos bugs e problemas precisam ser resolvidos ainda.
Inclusive uma reescrita já está nos planos.

### Problemas conhecidos:
- Validação por sessão com cookie: Isso inviabiliza um balanceamento de carga (seria necessário ativar stickbit);
- Reprodução de vídeo: A tag video possui um problema e não reproduz corretamente;
- Reprodução de áudio: Por enquanto não está sendo feito streaming e o audio precisa ser carregado inteiro antes de tocar;
- Sanity checks;
- Code styling;

Mas o software já está utilizável e funciona bem! :)
Espero que possa ajudá-los!
