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
 - Um conjunto de icoes de bandeiras (indico este: http://www.icondrawer.com/flag-icons.php)

### Como ele funciona

É relativamente simples, o sistema é divido em 4 partes:
 1. O cliente mobile
 2. O Servidor REST (servidor de consulta)
 3. O Banco de Dados
 4. A interface de administração

![Como funciona](https://raw.githubusercontent.com/allangood/virtualguide/master/site_media/virtualguide_pt.jpg "Como Funciona")

1. Os expositores inserem os dados no banco de dados através da interface Web;
 1. Os administradores do aplicativo fazem as customizações necessárias;
 2. Os administradores imprimem o código de Checkin e colocam na entrada da exposição;
2. Os visitantes capturam o código de Checkin antes de entrar na exposição;
3. Os visitantes capturam os códigos (QR Code) dos items;
4. O aplicativo envia o código ao servidor de consulta (REST);
 1. O servidor REST valida as requisições, consulta o banco de dados e devolve uma resposta;
5. O aplicativo mostra os dados recebidos pelo servidor (texto, foto, audio e video)

### Screenshots

#### Interface Mobile
Mobile Application: ![Mobile App](https://play.google.com/store/apps/details?id=com.ionicframework.virtualguide960037 "Android Version")

#### Interface Web
![Login](https://raw.githubusercontent.com/allangood/virtualguide/master/site_media/AdminVirt_01.png "Login")
![Inicio](https://raw.githubusercontent.com/allangood/virtualguide/master/site_media/AdminVirt_02.png "Inicio")
![Linguas](https://raw.githubusercontent.com/allangood/virtualguide/master/site_media/AdminVirt_04.png "Linguas")
![Configuracoes](https://raw.githubusercontent.com/allangood/virtualguide/master/site_media/AdminVirt_05.png "Configuracoes")

### FAQ
**Por que utilizar um banco NoSQL?**

Porque não preciso de um banco SQL, simples assim. As bases não precisam de relacionamentos nem de constraints, são simples repositórios. Portanto, são casos típicos de uso de bases NoSQL.

**Por que usar GridFS?**

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
- [X] Reescrever a interface web usando Bootstrap 3 (feito!) (adminvirt)
- [X] Criar sistema de autorização e autenticação (feito) (adminvirt)
- [ ] Criar sistema de plugins para autenticação e autoreização (WiP)
- [ ] Criar uma tela para login ao realizar o Checkin (mobile_app) (WiP)
- [ ] Adicionar enquete ao sair do aplicativo (feedback para o expositor) (mobile_app) (WiP)
- [ ] Reescrever o aplicativo usando Ionic2 / AngularJS2 (mobile_app) (NS)

* WiP: Work in Progress
* NS: Not Started
