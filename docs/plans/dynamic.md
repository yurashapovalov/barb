Plan: Modular Prompt Architecture                                   
                                                                     
 Problem                                                             
                                                                     
 Текущий промпт — одна строка в prompt.py. Три проблемы из e2e (3/7  
 PASS):                                                              
                                                                     
 1. Over-confirmation — на follow-up ("а отдельно для гэпов вверх и  
 вниз?") модель спрашивает "Продолжить?" вместо того чтобы сразу     
 работать. Инструкция "wait for confirmation" не различает первый    
 вопрос и follow-up.                                                 
 2. Expression reference вне контекста — модель вызывает             
 get_expression_help каждый раз, тратя round-trip. Reference         
 короткий (~46 строк) — можно держать в промпте.                     
 3. Workspace state invisible — когда recipe восстанавливает         
 workspace (session=RTH, timeframe=daily, columns=[range, gap]),     
 модель не знает об этом и вызывает set_session/set_timeframe        
 заново.                                                             
                                                                     
 Плюс промпт будет расти: индикаторы, бэктесты, RAP — нужна          
 модульная структура.                                                
                                                                     
 Solution                                                            
                                                                     
 Разбить промпт на секции-функции. Каждая секция — pure function →   
 str. Ассемблер собирает промпт под конкретный запрос (с recipe или  
 без).                                                               
                                                                     
 Architecture                                                        
                                                                     
 Section functions                                                   
                                                                     
 Файл: assistant/prompt.py (тот же файл, рефакторинг).               
                                                                     
 build_system_prompt(instrument, recipe=None)                        
 ├── _section_role(instrument, config)       # кто ты, тон           
 ├── _section_context(instrument, config)    # символ, биржа, даты,  
 сессии                                                              
 ├── _section_workspace(recipe)              # [conditional] текущее 
  состояние workspace                                                
 ├── _section_instructions()                 # pipeline,             
 confirmation flow                                                   
 ├── _section_constraints(config)            # ограничения           
 ├── _section_expressions()                  # expression reference  
 (из expressions.md)                                                 
 └── _section_examples(config)               # 4 tool chain примера  
                                                                     
 Каждая секция оборачивается в XML тег (<role>, <context>,           
 <workspace>, etc.).                                                 
                                                                     
 Key changes                                                         
                                                                     
 1. _section_instructions — fix over-confirmation:                   
 First question in conversation:                                     
   → Describe what you'll compute in ONE sentence. Wait for          
 confirmation.                                                       
                                                                     
 Follow-up (history exists):                                         
   → Execute immediately. No confirmation needed.                    
                                                                     
 2. _section_workspace(recipe) — dynamic, only when recipe exists:   
 <workspace>                                                         
 Pre-loaded state from previous turn:                                
 - Session: RTH (09:30-16:15)                                        
 - Timeframe: daily                                                  
 - Columns: range = high - low, gap = open - prev(close)             
 Do NOT call set_session, set_timeframe, or add_column for these —   
 they're already applied.                                            
 </workspace>                                                        
                                                                     
 3. _section_expressions — inline expression reference:              
 Читаем expressions.md один раз при импорте, вставляем в промпт.     
 Модель больше не нужно вызывать get_expression_help. ~46 строк =    
 ~200 tokens — дешевле чем extra round-trip.                         
                                                                     
 4. _section_examples — добавить пример follow-up без confirmation:  
 Example 5 — follow-up:                                              
 User: What percentage of gap ups fill?                              
 Assistant: ...72.6%...                                              
 User: and for gap downs separately?                                 
 [set_session(RTH), set_timeframe(daily)] — parallel                 
 [add_column("gap", "open - prev(close)")]                           
 ...                                                                 
 Assistant: Gap downs fill 68% of the time — less reliable than gap  
 ups.                                                                
                                                                     
 chat.py change                                                      
                                                                     
 build_system_prompt получает recipe:                                
 # В chat_stream, перед первым API call:                             
 system_prompt = build_system_prompt(self.instrument, recipe=recipe) 
                                                                     
 Промпт больше не кэшируется в __init__ — строится динамически       
 per-request.                                                        
                                                                     
 Files to change                                                     
 File: assistant/prompt.py                                           
 Change: Разбить на section functions, добавить workspace section,   
   inline expressions, fix confirmation flow                         
 ────────────────────────────────────────                            
 File: assistant/chat.py                                             
 Change: Строить промпт per-request с recipe, убрать                 
   self.system_prompt из __init__                                    
 ────────────────────────────────────────                            
 File: tests/test_prompt.py                                          
 Change: Обновить тесты для нового промпта                           
 Ничего не удаляем. expressions.md остаётся (используется и в        
 промпте, и в get_expression_help tool).                             
                                                                     
 Implementation order                                                
                                                                     
 1. assistant/prompt.py — section functions + assembler              
 2. assistant/chat.py — dynamic prompt per request                   
 3. tests/test_prompt.py — обновить                                  
 4. e2e test — проверить improvement   