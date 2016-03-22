# Virtual Guide

O público alvo deste projeto são os expositores e visitantes de exposições.

**Expositor:**

Para melhorar a experiência dos seus visitantes.
Basta imprimir e colocar em cada obra um código (QR Code) que o usuário pode, com seu próprio smartphone ou tablet, capturar e visualizar informações, imagem, vídeo e aúdio na língua dele associado àquela obra. Isso não seria ótimo?
Além disso, você recebe (expositor) recebe feedback sobre as visualizações.
Você poderá responder às seguintes perguntas:
- Quais são as obras mais visualizadas?
- Quais são as obras que os visitantes mais gostam?
Isso irá te auxiliar a melhorar campanhas de marketing e possivelmente alavancar negócios.

**Visitante**

O visitante não precisa instalar vários aplicativos em seus telefone. Um aplicativo para todas as exposições do Mundo!
Se for a um Museu Internacional ou um Museu local, na sua cidade mesmo, basta abrir o VirtualGuide, realizar o Checkin e aproveitar a visita!
Não seria ótimo receber informações para cada item que está visualizando?

Isso é o VirtualGuide! Um aplicativo único para todas as exposições! E todos os expositores/Museus podem utilizar livremente!

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
 2) O Servidor REST (servidor de consulta)
 3) O Banco de Dados
 4) A interface de administração

![Como funciona](https://raw.githubusercontent.com/allangood/virtualguide/master/site_media/virtualguide_pt.jpg "Como Funciona")

1) O administrador insere os dados no banco de dados
2) O cliente faz requisições ao servidor REST
3) O servidor REST valida as requisições, consulta o banco de dados e devolve uma resposta.

### FAQ
*Por que utilizar um banco NoSQL?*
Porque não preciso de um banco SQL, simples assim. As bases não precisam de relacionamentos nem de constraints, são simples repositórios. Portanto, são casos típicos de uso de bases NoSQL.

*Por que usar GridFS?*
Quando imaginei este aplicativo, pensei no Museu do Louvre, com milhares de obras e uma infinidade de usuário o tempo todo!
O MongoDB e GridFS foram feitos com a idea de Cluster. Crescimento horizontal. Caso seja necessário utilizar vários servidores, distribuir os arquivos em diversos servidores seria um problema. Replicação, rsync, GFS, OCFS, storage externo... Isso dificulta e encarece uma solução simples. Com o MongoDB e GridFS, basta adicionar servidores com discos internos e pronto. Simples, rápido, barato e muito mais eficiente. Para quê complicar? Keep It Simple - KIS right? :)

**Por que Ionic?**

É simples, multiplataforma e se encaixa perfeitamente nas minhas necessidades.


**Por que Software Livre?**

Sério? Por que não seria? AngularJS é Software Livre, Ionic também, o Debian Linux (ou GNU/Linux para a FSF) onde desenvolvo é livre, o Atom que uso pra editar é livre! As milhares de pessoas que respondem a forums na Internet não cobram nem licenciam suas respostas... Qual seria a razão de não devolver à comunidade o que aprendi com eles?

### Problemas conhecidos:
- ~~Problema com streaming do audio~~ (resolvido)
- Reprodução de vídeo: A tag video possui um problema e não reproduz corretamente;

Espero que possa ajudá-los!


### TODO:
- [X] Reescrever a interface web usando Bootstrap 3 (feito!)
- [ ] Criar uma tela para login ao realizar o Checkin
- [ ] Adicionar enquete ao sair do aplicativo (feedback para o expositor)
- [ ] Reescrever o aplicativo usando Ionic2 / AngularJS2
