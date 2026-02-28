"""
Módulo 3 - Validação de Contatos
Endpoint para validar número de WhatsApp de comprador/vendedor via Evolution API
"""
import random
import string
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.validation import ContactValidation
from app.services.evolution_service import send_validation_message, check_whatsapp_number

router = APIRouter(prefix="/api", tags=["Module 3 - Validate Contact"])


class ValidateContactRequest(BaseModel):
    phone: str
    order_id: Optional[str] = None
    name: Optional[str] = ""  # Nome para personalizar mensagem


class ValidateContactResponse(BaseModel):
    success: bool
    status: str
    message: str
    validation_id: Optional[str] = None
    expires_at: Optional[datetime] = None


class VerifyCodeRequest(BaseModel):
    validation_id: str
    code: str


class VerifyCodeResponse(BaseModel):
    success: bool
    status: str
    message: str
    validated: bool = False


def generate_validation_code() -> str:
    """Gera código de 4 dígitos numéricos"""
    return ''.join(random.choices(string.digits, k=4))


def generate_validation_id() -> str:
    """Gera ID único para validação"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"val_{timestamp}_{random_suffix}"


def format_phone(phone: str) -> str:
    """Formata número de telefone para padrão internacional"""
    # Remove caracteres não numéricos
    phone = ''.join(filter(str.isdigit, phone))
    
    # Se não começar com 55 (Brasil), adiciona
    if not phone.startswith('55'):
        phone = '55' + phone
    
    return phone


@router.post("/validate-contact", response_model=ValidateContactResponse)
async def validate_contact(
    request: ValidateContactRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Inicia processo de validação de contato via WhatsApp.
    
    Envia código de 4 dígitos via WhatsApp e armazena registro no banco.
    O código expira em 5 minutos.
    
    Requisição:
    {
        "phone": "11999999999",
        "order_id": "123",
        "name": "João" (opcional)
    }
    
    Resposta:
    {
        "success": true,
        "status": "pending",
        "message": "Código enviado para WhatsApp",
        "validation_id": "val_...",
        "expires_at": "2024-..."
    }
    """
    try:
        # Formata telefone
        formatted_phone = format_phone(request.phone)
        
        # Verifica se número existe no WhatsApp
        check_result = check_whatsapp_number(formatted_phone)
        if not check_result.get("exists", True):  # Se falhar na verificação, continua mesmo assim
            print(f"[VALIDATE] Aviso: Número {formatted_phone} pode não existir no WhatsApp")
        
        # Gera código e ID
        code = generate_validation_code()
        validation_id = generate_validation_id()
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        # Salva no banco de dados
        validation = ContactValidation(
            validation_id=validation_id,
            order_id=request.order_id,
            phone=formatted_phone,
            code=code,
            status="pending",
            attempts=0,
            max_attempts=3,
            expires_at=expires_at
        )
        db.add(validation)
        db.commit()
        
        # Envia mensagem em background (não bloqueia resposta)
        background_tasks.add_task(
            send_validation_message,
            phone=formatted_phone,
            code=code,
            name=request.name or ""
        )
        
        print(f"[VALIDATE] Código {code} gerado para {formatted_phone}, ID: {validation_id}")
        
        return ValidateContactResponse(
            success=True,
            status="pending",
            message="Código de validação enviado para seu WhatsApp",
            validation_id=validation_id,
            expires_at=expires_at
        )
        
    except Exception as e:
        print(f"[VALIDATE] Erro: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar validação: {str(e)}")


@router.post("/validate-contact/verify", response_model=VerifyCodeResponse)
async def verify_code(
    request: VerifyCodeRequest,
    db: Session = Depends(get_db)
):
    """
    Verifica código informado pelo usuário.
    
    Requisição:
    {
        "validation_id": "val_...",
        "code": "1234"
    }
    
    Resposta:
    {
        "success": true,
        "status": "validated",
        "message": "Código confirmado com sucesso",
        "validated": true
    }
    """
    try:
        # Busca validação no banco
        validation = db.query(ContactValidation).filter(
            ContactValidation.validation_id == request.validation_id
        ).first()
        
        if not validation:
            raise HTTPException(status_code=404, detail="Validação não encontrada")
        
        # Verifica se já foi validado
        if validation.status == "validated":
            return VerifyCodeResponse(
                success=True,
                status="validated",
                message="Contato já validado anteriormente",
                validated=True
            )
        
        # Verifica se expirou
        if validation.is_expired():
            validation.status = "expired"
            db.commit()
            return VerifyCodeResponse(
                success=False,
                status="expired",
                message="Código expirado. Solicite novo código.",
                validated=False
            )
        
        # Incrementa tentativas
        validation.attempts += 1
        db.commit()
        
        # Verifica se excedeu tentativas
        if validation.attempts > validation.max_attempts:
            validation.status = "failed"
            db.commit()
            return VerifyCodeResponse(
                success=False,
                status="failed",
                message="Número máximo de tentativas excedido. Solicite novo código.",
                validated=False
            )
        
        # Verifica código
        if request.code == validation.code:
            validation.status = "validated"
            validation.validated_at = datetime.utcnow()
            db.commit()
            
            print(f"[VERIFY] Código confirmado para {validation.validation_id}")
            
            return VerifyCodeResponse(
                success=True,
                status="validated",
                message="Código confirmado com sucesso! Contato validado.",
                validated=True
            )
        else:
            remaining = validation.max_attempts - validation.attempts
            return VerifyCodeResponse(
                success=False,
                status="pending",
                message=f"Código incorreto. {remaining} tentativas restantes.",
                validated=False
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[VERIFY] Erro: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao verificar código: {str(e)}")


@router.get("/validate-contact/status/{validation_id}")
async def validation_status(validation_id: str, db: Session = Depends(get_db)):
    """
    Consulta status de uma validação
    """
    try:
        validation = db.query(ContactValidation).filter(
            ContactValidation.validation_id == validation_id
        ).first()
        
        if not validation:
            raise HTTPException(status_code=404, detail="Validação não encontrada")
        
        # Verifica se expirou
        if validation.status == "pending" and validation.is_expired():
            validation.status = "expired"
            db.commit()
        
        return {
            "validation_id": validation_id,
            "status": validation.status,
            "phone": validation.phone,
            "attempts": validation.attempts,
            "max_attempts": validation.max_attempts,
            "created_at": validation.created_at,
            "expires_at": validation.expires_at,
            "validated_at": validation.validated_at,
            "is_expired": validation.is_expired(),
            "can_retry": validation.can_retry()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-contact/resend")
async def resend_validation(
    validation_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Reenvia código de validação (gera novo código)
    """
    try:
        # Busca validação anterior
        old_validation = db.query(ContactValidation).filter(
            ContactValidation.validation_id == validation_id
        ).first()
        
        if not old_validation:
            raise HTTPException(status_code=404, detail="Validação não encontrada")
        
        # Invalida registro anterior
        old_validation.status = "expired"
        db.commit()
        
        # Cria nova validação
        new_code = generate_validation_code()
        new_validation_id = generate_validation_id()
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        new_validation = ContactValidation(
            validation_id=new_validation_id,
            order_id=old_validation.order_id,
            phone=old_validation.phone,
            code=new_code,
            status="pending",
            attempts=0,
            max_attempts=3,
            expires_at=expires_at
        )
        db.add(new_validation)
        db.commit()
        
        # Envia nova mensagem
        background_tasks.add_task(
            send_validation_message,
            phone=old_validation.phone,
            code=new_code
        )
        
        return {
            "success": True,
            "status": "pending",
            "message": "Novo código enviado para WhatsApp",
            "validation_id": new_validation_id,
            "expires_at": expires_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
