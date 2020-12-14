# Building Persona API with FastAPI

In this training we will learn how to use the framework FastAPI by building a Persona API

FastAPI is a new Python framework for building APIs that is fast, powerfull and enjoyable\
to use. You can check its documentation [here](https://fastapi.tiangolo.com/)

## **Persona API**

The idea is to build an API that provides the following features:

* Add new Personas
* Get a list or just one Persona
* Update or delete the Persona
* Add Direccion and assign it to an Persona
* Get a list or just one Direccion
* Get the Persona's Mercado Libre profile

This is how our project structure will look like:

```
├──/app
│  ├──/clients
│  ├──/database
│  ├──/handlers
│  ├──/models
│  ├──/routers
│  ├──/settings
│  ├──/utils
│  └── main.py
```

## Getting Started

First things first, lets install FastAPI with all the dependencies.\
For doing this we can run the following command:  

`$ pip install fastapi[all]`

Now that we have FastAPI installed we can start coding!

## Database Data Models

Lets start setting up our DataBase Models (lets call it schemas) and the configuration for the\
DataBase connection.\
To do all of this, we are using the toolkit SQLAlchemy (It's already installed with the FastAPI\
Package) and a PostgreSQL DataBase (you can use SQLite or any other DataBase).

In the file `/database/db.py` we are going to build the code that handles the\
connection to the database:

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


DATABASE_URL = 'postgresql://user:password@postgresserver/db'


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

Here we are doing several things:

* Creating a SQLAlchemy `engine` that we will use later (you can check [this](https://docs.sqlalchemy.org/en/13/core/engines.html) for more info).
* Creating a `SessionLocal` class using the function `sessionmaker` (each instance of this class\
 will be an actual database session).
* Creating a `Base` class with the `declarative_base()` function, all our schemas (DataBase Models)\
will inherit from this class.

Now we can go and create our schemas!\
We will have this `/app/database/schemas.py` file where our schemas are going to be

```python
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database.db import Base


class Personas(Base):
    __tablename__ = 'personas'
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    apellido = Column(String)
    direccion_id = Column(Integer, ForeignKey("direcciones.id"), nullable=True)
    perfil_meli_id = Column(Integer, nullable=True)

    def serialize(self):
        return {"id": self.id,
                "nombre": self.nombre,
                "apellido": self.apellido,
                "direccion_id": self.direccion_id,
                "perfil_meli_id": self.perfil_meli_id}


class Direcciones(Base):
    __tablename__ = 'direcciones'
    id = Column(Integer, primary_key=True, index=True)
    calle = Column(String)
    numero = Column(Integer)

    def serialize(self):
        return {"id": self.id,
                "calle": self.calle,
                "numero": self.numero}
```

These are clases that inherit from the Base class we have created in the previous file.

>*Here we call these DataBase Models as Schemas, but some people preferes to call them Models*

## Body and Response Models

When we have to receive or send data from our API, we uses request and response bodies.

To declare a body, either request or response, we use [Pydantic](https://pydantic-docs.helpmanual.io/) models and all the benefits it brings.\
And now we are going to create models for each of our bodies...

In the folder `/app/models/` we will create a file for each group of models:

*The direccion models will be in `/app/models/direccion.py`:*

```python
from pydantic import BaseModel


class DireccionBase(BaseModel):
    calle: str
    numero: int


class Direccion(DireccionBase):
    id: int

    class Config:
        orm_mode = True

```

*The persona models will be in `/app/models/persona.py`:*

```python
from pydantic import BaseModel
from typing import Optional
from models.direccion import Direccion


class PersonaBase(BaseModel):
    nombre: str
    apellido: str
    direccion_id: Optional[int]


class Persona(PersonaBase):
    id: int
    direccion: Optional[Direccion]

    class Config:
        orm_mode = True
```

These classes inherit from the pydantic's BaseModel so all their attributes can be validated using\
python type annotations.
>*(in some docs you will find this models named as schemas)*

Lets look at the Persona models, here we are using the PersonaBase class to represent the data that\
comes from the client *(request body)*, and the Persona class is for the data that our API sends *(response body)*.\
And we are doing the same in the Direccion models

The Config class is used to provide configurations to Pydantic.
>*Pydantic's orm_mode will tell the Pydantic model to read the data even if it is not a dict,\
 but an ORM model (or any other arbitrary object with attributes).*

## Repositories

Now that we have the models and schemes for all our incoming and outgoing data declared, we can start\
doing some queries to the db

A good way to handle the queries to the DB is by applying the Repository Pattern.\
This pattern consist of encapsulating the logic required to acces the data in class or component

*the direccion repository is going to be in `/app/database/repositories/direccion.py`*

```python
from typing import List
from sqlalchemy.orm.session import Session
from models.direccion import Direccion, DireccionBase
from database.schemas import Direcciones


class DireccionRepository:

    @staticmethod
    async def get_direccion(db: Session, id: int) -> Direccion:
        return db.query(Direcciones).filter(Direcciones.id == id).first().serialize()

    @staticmethod
    async def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Direccion]:
        direcciones = [d.serialize() for d in db.query(
            Direcciones).offset(skip).limit(limit).all()]

        return direcciones

    @staticmethod
    async def create(db: Session, direccion: DireccionBase) -> Direccion:
        db_direccion = Direcciones(**direccion.dict())
        db.add(db_direccion)
        db.commit()
        db.refresh(db_direccion)

        return db_direccion.serialize()

```

*the persona repository is going to be in `/app/database/repositories/persona.py`*

```python
from typing import List
from sqlalchemy.orm.session import Session
from models.persona import Persona, PersonaBase
from database.schemas import Personas


class PersonaRepository:

    @staticmethod
    async def get_persona(db: Session, id: int) -> Persona:
        persona = db.query(Personas).filter(Personas.id == id).first()
        return persona

    @staticmethod
    async def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Persona]:
        personas = db.query(Personas).offset(skip).limit(limit).all()
        return personas

    @staticmethod
    async def create(db: Session, persona: PersonaBase):
        db_persona = Personas(**persona.dict())

        if db_persona.direccion_id == 0:
            db_persona.direccion_id = None


        db.add(db_persona)
        db.commit()
        db.refresh(db_persona)

        return db_persona

    @staticmethod
    async def update(db: Session, id: int, persona: PersonaBase):
        persona = Personas(**persona.dict())
        db_persona = db.query(Personas).filter(Personas.id == id).first()
        db_persona.nombre = persona.nombre
        db_persona.apellido = persona.apellido
        db_persona.direccion_id = persona.direccion_id

        if db_persona.direccion_id == 0:
            db_persona.direccion_id = None

        db.commit()
        db.refresh(db_persona)

        return db_persona
```

## Routers

Lets start working on our endpoints!

We are goint to put everything together here, on our routers.\
If you have worked with Flask, the FastAPI way to declare routes will be familiar to you.\

> But first lets take a quick look to the **Dependency Injection** in FastAPI:\
> _""**Dependency Injection**" means, in programming, that there is a way for your code\
> (in this case, your path operation functions) to declare things that it requires\
> to work and use: "dependencies"."_
>
> In this case we will declare a Dependency, a function that gives us a DataBase session:\
> *(I will teach you how to use apply it in the routers)*
>
> *this code will be in `/app/dependencies.py`*
>
> ```python
>async def get_db():
>    db = SessionLocal()
>    try:
>        yield db
>    finally:
>        db.close()
> ```

Lets take a look to the direccion router!

*the direccion router is going to be in `/app/routers/direccion.py`*

```python
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.direccion import Direccion, DireccionBase
from dependencies import get_db
from database.repositories.direccion import DireccionRepository


router = APIRouter()


@router.get("/direccion/list/", response_model=List[Direccion])
async def get_direcciones(db: Session = Depends(get_db)):
    direcciones = await DireccionRepository.get_all(db=db)

    return direcciones


@router.get("/direccion/{id}", response_model=Direccion)
async def get_direccion(id: int, db: Session = Depends(get_db)):
    direccion = await DireccionRepository.get_direccion(db=db, id=id)
    if not direccion:
        raise HTTPException(status_code=404, detail='Direccion Not Found')

    return direccion


@router.post("/direccion/create/", response_model=Direccion)
async def create_direccion(direccion: DireccionBase, db: Session = Depends(get_db)):
    direccion = await DireccionRepository.create(db=db, direccion=direccion)

    return direccion
```

The first important thing here is the a APIRouter instance (`router = APIRouter()`).\
That instance will be used to create our paths

So, lets take a look to the path declaration...

```python
@router.get("/direccion/{id}", response_model=Direccion)
async def get_direccion(id: int, db: Session = Depends(get_db)):
    direccion = await DireccionRepository.get_direccion(db=db, id=id)
    if not direccion:
        raise HTTPException(status_code=404, detail='Direccion Not Found')

    return direccion
```

Here we are doing a few things:

* First we are defining this endpoint, and declaring that it will be called but the GET method *(`@router.get(...`)*,\
then the path *(`..."/direccion/{id}",...`)*, and with *(`...response_model=Direccion)`)* we are saying that this endpoint\
will return a body with the Direccion Model *(the one defined in `/app/models/direccion.py`)*

* The following is the parameters declarations, if you look at the path of this endpoint, you will notice that\
we are receiving an id *(`.../{id}"...`)*, so we have to do the same in the function parameters *(`...(id: int...`)*\
and also another important parameter, the database session that we will need to use, we are getting this session\
using the Dependency get_db *(`...db: Session = Depends(get_db)):`)*, thats the FastAPI way to consume dependencies\
*(that dependency is in the file `/app/dependencies.py`)*

* Then the logic of the endpoint, we get the direccion received in the path by `id` by using DireccionRepository\
*(`direccion = await DireccionRepository.get_direccion(db=db, id=id)`)*, if there is no direccion with that id we raise\
an error *(`raise HTTPException(status_code=404, detail='Direccion Not Found')`)*.\
And finally, we return the direccion *(`return direccion`)*

And, for the Persona endpoints we are doing a pretty similar thing.

```python
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.persona import Persona, PersonaBase
from database.repositories.persona import PersonaRepository
from dependencies import common_params, get_db


router = APIRouter(tags=['persona'])


@router.get("/persona/", response_model=List[Persona])
async def get_personas(db: Session = Depends(get_db)):
    personas = await PersonaRepository.get_all(db=db)

    return personas


@router.get("/persona/{id}/", response_model=Persona)
async def get_persona(id: int, db: Session = Depends(get_db)):
    persona = await PersonaRepository.get_persona(db=db, id=id)
    if not persona:
        raise HTTPException(status_code=404, detail='Persona Not Founf')

    return persona


@router.put("/persona/update/{id}/", response_model=Persona)
async def update_persona(id: int, persona: PersonaBase, db: Session = Depends(get_db)):
    if not await PersonaRepository.get_persona(db=db, id=id):
        raise HTTPException(status_code=404, detail='Persona To Update Not Found')
    updated_persona = await PersonaRepository.update(db, id, persona)

    return updated_persona


@router.post("/persona/create/", response_model=Persona)
async def create_persona(persona: PersonaBase, db: Session = Depends(get_db)):
    persona = await PersonaRepository.create(db=db, persona=persona)

    return persona
```

Anyway, here we have something interesting to mention, when creating the instance of the router\
we can set some parameters that will apply to all the endpoints in this router, in this case\
we are setting a tag that will help to order our endpoints when we load the auto generated docs\
that FastAPI provide us using swagger *(`router = APIRouter(tags=['persona'])`)*/
*(you can find the docs in the path /docs when the app is up and running)*

## *Running the APP*

Finally!! We are going to start running our APP!

But first, lets create the *main* file that handles everything to work together

```python
from fastapi import FastAPI
from routers import persona, direccion
from database.schemas import Base
from database.db import engine


app = FastAPI()


Base.metadata.create_all(bind=engine)
app.include_router(direccion.router)
app.include_router(persona.router)

```

lets explain this file:

* With `app = FastAPI()` we are creating an instance of FastAPI that will be our main app
* `Base.metadata.create_all(bind=engine)` is to create the DB Tables *(take a look to [Alembic docs](https://alembic.sqlalchemy.org/en/latest/))*
* And then with `app.include_router(direccion.router)` and `app.include_router(persona.router)`\
we are including the router that we have created before, to this main app

**And now.. Lets Run It!!**

for doing this, type on you terminal:

``` bash
uvicorn app.main:app --reload
```

Thats it.. We have our APP up and running!

Please, take a look to the [Source Code](https://gitlab.com/ecraft.com.ar/031_jovenes_talentos_kevin/-/tree/master/FastAPI),it will be very helpful for you, also, there are many\
things implemented that we haven't talked about yet.
In the next sections we will teach you about those things, but please, have the source code handy

------

## **Advanced Stuff**

We have finished the base of our app, but there still are more things that we can do...

This section is more advanced, so im not explaining everything that we are doing like in the\
previous sections, and it is assumed that you are looking at the [Source Code](https://gitlab.com/ecraft.com.ar/031_jovenes_talentos_kevin/-/tree/master/FastAPI).

## Response Handler

The idea of this response handler is to have a body format for all our responses with the\
information that we want to give and in the way we want.

The responses handler is a class GeneralJSONResponse which is used to replace the default\
response class. It automatically receives all the responses sent by the routers and format\
them using the Model 'Responses' that you can find on the file `/app/models/responses.py`

*`/app/handlers/responses.py`*

```python
class GeneralJSONResponse(UJSONResponse):
    '''
    This class inherits from UJSONResponse which is a Response Class provided by FastAPI
    UJSON is an faster JSON encoder for Python
    '''

    __slots__ = []

    def __init__(self, detail='', **kwargs):
        values = Helpers.get_values(kwargs)  
        resp_body = Helpers.get_response(
            status_code=values['status_code'],
            content=values['content'],
            detail=detail)

        response = Response(**resp_body)

        super(GeneralJSONResponse, self).__init__(
            status_code=values['status_code'], content=response.dict())
```

Here we have our GeneralJSONResponse class that inherits from UJSONResponse, so it has all its parent\
functionaities and we are only adding the code we need to have the custom response body that we want.

The `get_values` and `get_response` functions are the ones that parse and format the values coming from\
the routers, giving us the final body as a dict *(check the functions in `/app/utils/responses.py`)*.

Then we have the `response = Response(**resp_body)` line in which we get the Response Model object with\
our data to finally send it to its parent class

## Authentication with JWT

For the Authentication I decided to use JWT instead of OAuth2(The one that is on FastAPI docs),\
because JWT is easy to implement and as we dont need the whole Authentication flow that comes with\
OAuth2, we can use the Json Web Tokens and do the validations for the authentications on our own.

For this, we have created new **repositories**, **models**, and **routers**, find them in the [Source Code](https://gitlab.com/ecraft.com.ar/031_jovenes_talentos_kevin/-/tree/master/FastAPI).

*We have the token creation in `/app/utils/user_auth.py`*

```python
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm.session import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from database.repositories.user import UserRepository
from settings.config import SECRET_KEY, ALGORITHM
from models.user import UserCreate, User
from models.token import Token


pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


async def verify_password(plain_pwd: str, hashed_pwd: str) -> bool:
    '''
    Verify if the plain text password is correct by comparing it 
    to the hashed password
    Receives plain text password(str), hashed password(str) 
    Returns Bool
    '''
    return pwd_context.verify(plain_pwd, hashed_pwd)


async def sanitize_password(user: UserCreate) -> UserCreate:
    '''
    Update its password value by hashing it, so now its secured
    and can be stored in DB
    Receives user(UserCreate) 
    Returns UserCreate
    '''
    user.password = pwd_context.hash(user.password)
    return user


async def authenticate_user(db: Session, username: str, password: str) -> User:
    '''
    Authenticate the user by checking if the user exists and verifying its password
    Receives db(Session), username(str), password(str)
    returns User
    '''
    user = await UserRepository.get_user(db, username)
    if not user:
        return False
    if not await verify_password(password, user.password):
        return False
    return user


async def create_access_token(username: str, expires_delta: Optional[timedelta] = None) -> Token:
    '''
    Creates an access token for the received user, by default the token will expire in
    1500 minutes, it can be changed by passing the expires_delta parameter
    Receives username(str), expires_delta(timedelta)
    returns Token
    '''
    data = {'usr': username}
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=1500)
    to_encode.update({"exp": expire})
    token = {'access_token': jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM),
             'token_type': 'bearer'}
    return token
```

*And its applied in a dependency `/app/dependencies.py`*

```python

async def get_token(Authorization: str = Header(None)):
    '''
    Parse the Authorization Header and get the Token from it.
    Receives Authorization(str)(comes in the header of the request)
    Returns token(str)
    '''
    if not Authorization:
        raise await credentials_exception()
    token = Authorization.split()
    if token[0] != 'bearer':
        raise await credentials_exception()

    return token[1]


async def get_user_authentication(token: str = Depends(get_token), db: Session = Depends(get_db)):
    '''
    Authenticate the user by validatin its token and then checking if it exists in the DB
    Receives token(str)(from the dependency get_token), db(Session)(from the dependency get_db)
    Returns user
    '''
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("usr")
        if username is None:
            raise await credentials_exception()
        token_data = TokenData(username=username)
    except JWTError:
        raise await credentials_exception()

    user = await UserRepository.get_user(db, username=token_data.username)
    if user is None:
        raise await credentials_exception()

    return user
```

## Middleware for Auth

If we want to do the Authentication in the middleware we can do something like this

```python
class BasicAuthBackend(AuthenticationBackend):
    async def authenticate(self, request):
        if "Authorization" not in request.headers:
            return credentials_exception()
        user = await get_current_user(request.headers["Authorization"])

        return AuthCredentials(["authenticated"]), SimpleUser(user)
```

This is a class that inherit from Starlettes AuthenticationBackend and should be use as middleware with\
AuthenticationMiddleware, like this

``` python
app = FastAPI()

app.add_middleware(AuthenticationMiddleware, backend=BasicAuthBackend())
```

And then using `request.user.is_authenticated` we can validate inside the routes if the user is\
authenticated, and then decide if redirect or not.

But, validating in each route if the user is authenticated or not, would be a headache in the long term.\
Anyway I've found two other ways to do that:

* Doing paths validations inside the route:

```python
if not request.user.is_authenticated:
    if '/auth/login' in request.url:
        return response
    else:
        return RedirectResponse(url='/auth/login')
```

> Its ok if we want only to exclude this path, but if we have some other paths that dont need authentication
  we would end up with a lot of validations

* Another way is to have multiple apps and then mount them together, something like this:

```python
app1.include_router(direccion.router, prefix="/direccion",)
app1.include_router(persona.router, prefix="/persona",)
app1.add_middleware(AuthenticationMiddleware, backend=BasicAuthBackend())

app2.include_router(auth.router, prefix="/auth",)

app.mount(app1, "/")
app.mount(app2, "/users")
```

> Maybe this way is more friendlier, as we only have to include the routers in the correct app and thats it.\
But also we have another option...

## **Route Level Dependency**

In this case, we only have to do write `router = APIRouter(dependencies=[Depends(get_current_user)])` on our router file,\
and thats it.
With only that line we will apply the auth to the route.

In this Dependencies we can catch the Request and get a lot of usefull info, such as the URL (and its path, port, shceme),\
Headers, Query Params, Cookies, Body, and much more.

Here is an example, not a very useful one, but it helps to get the idea

```python
async def get_request(request: Request):
    if request.method == 'PATCH':
        raise HTTPException(status_code=405, detail='We dont believe in the PATCH method.')
```
