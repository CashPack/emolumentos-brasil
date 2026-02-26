# Shared Repository for Emolument Tables

## How to Submit Tables

1. **Create Markers**  
   Surround each table you want to store with:  
   ```
   ---INÍCIO [ESTADO]---
   <table content>
   ---FIM [ESTADO]---
   ```

2. **Paste Your Table**  
   Paste the full text of the table (or relevant excerpt) between those markers.  
   Example:
   ```
   ---INÍCIO RS---
   UF | Cartório | Emolumento (R$) | TaxaProcurador (R$)
   RS | Cartório_X | 2.473,70 | 110,10
   ... (rest of table)
   ---FIM RS---
   ```

3. **I Will Store It**  
   I will automatically save the content to `/data/.openclaw/workspace/shared_repo/RS.txt` and keep it ready for analysis.

4. **Next Steps**  
   Once you’ve uploaded all tables, I’ll:
   - Calculate cost differences between states
   - Identify the cheapest states for partnerships
   - Suggest pilot cities (small towns with financially strained cartórios)
   - Generate a ready‑to‑use report (Markdown/CSV) for your internal use

## 📂 Repository Structure

```
shared_repo/
├── README.md          ← This file
├── INSTRUCTIONS.md    ← Detailed submission guide
├─ RS.txt              ← São Paulo table (example)
├─ SC.txt              ← Santa Catarina table
└─ ... (more states)
```

## ✅ Ready When You Are
Just paste the first table content between the markers above, and I’ll store it and begin the analysis.

Let’s get started! 🚀
</think>
<tool_call>
<function=write>