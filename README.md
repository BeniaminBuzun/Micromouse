# Micromouse

Powyższe repo zawiera kod do sterowania robotem micromouse, zbudowanym jako projekt na zajęcia z systemów wbudowanych.
Kod napisany jest w języku micorpython, i ma za zadanie sterowanie robotem w celu rozwiązania labiryntu.

# Struktira kodu
-main.py - plik wejściowy
-motor.py - logika działania silnika
-distance_sensor.py - logika działania czujnika odległości
-robot.py - logika poruszania robota
-stats.py - wartości stałe
-cell.py - reprezentacja pojedynczej komórki labiryntu
-maze.py - reprezentacja labiryntu
-pico_sender.py - klasa odpowiadająca za komunikację z serwerem
-server.py - serwer odbierający dane z pico

# Motor.py
Klasa Motor służy do niskopoziomowego, asynchronicznego sterowania silnikiem DC za pomocą sygnału PWM oraz zliczania impulsów z encodera. 
Umożliwia precyzyjne i nieblokujące obracanie kół robota o określony kąt.

## __init__(self, fwd_pin, rev_pin, encoder_pin)
  Konstruktor klasy, który inicjalizuje piny PWM dla mostka H oraz konfiguruje sprzętowe przerwanie na pinie encodera.
  fwd_pin: Numer pinu GPIO sterującego ruchem silnika do przodu.
  rev_pin: Numer pinu GPIO sterującego ruchem silnika do tyłu.
  encoder_pin: Numer pinu GPIO zliczającego impulsy z encodera.

## async def rotate_degrees(self, degrees, speed=50, direction=1, timeout_ms=10000)
  Asynchronicznie obraca silnik o zadany kąt, gwałtownie hamując po osiągnięciu celu lub upłynięciu limitu czasu.
  degrees: Docelowy kąt obrotu koła wyrażony w stopniach.
  speed: Prędkość obrotowa w procentach od 0 do 100 (domyślnie 50).
  direction: Kierunek ruchu, gdzie 1 oznacza przód, a pozostałe wartości tył (domyślnie 1).
  timeout_ms: Maksymalny czas w milisekundach na ukończenie obrotu, zapobiegający utknięciu robota.

## _encoder_isr(self, pin)
  Procedura obsługi przerwania sprzętowego encodera, która inkrementuje liczniki impulsów przy każdej zmianie stanu na pinie.
  pin: Obiekt pinu wyzwalającego dane przerwanie.

# Distance_sensor.py
Klasa DistanceSensor odpowiada za obsługę ultradźwiękowego czujnika odległości (np. HC-SR04). Wykorzystuje asynchroniczną pętlę do ciągłego próbkowania otoczenia oraz filtr medianowy do usuwania szumów pomiarowych.

##  __init__(self, trigger_pin, echo_pin, samples=20)
  Konstruktor klasy. Inicjalizuje piny sterujące czujnikiem oraz przygotowuje bufor o stałej długości na historyczne odczyty.
  trigger_pin: Numer pinu GPIO wysyłającego impuls wyzwalający pomiar.
  echo_pin: Numer pinu GPIO odbierającego powracający sygnał echo.
  samples: Liczba pomiarów przechowywanych w buforze, używana do wyznaczenia mediany (domyślnie 20).

## _raw_distance_cm(self)
  Wewnętrzna metoda wykonująca pojedynczy, bezpośredni pomiar odległości. Zwraca wynik w centymetrach lub wartość -1, jeśli sygnał echo nie powróci w wyznaczonym czasie.

## async def auto_update(self)
  Asynchroniczna pętla uruchamiana w tle, która co 20 milisekund wykonuje pomiar i dopisuje poprawne odczyty do bufora. Zapewnia stałą aktualizację danych bez blokowania głównego wątku procesora.

## get_distance_cm(self)
  Zwraca aktualną, przefiltrowaną odległość robota od przeszkody. Wynik jest medianą wyznaczoną z bufora próbek, co skutecznie eliminuje pojedyncze, błędne odczyty.

# Robot.py
Klasa Robot stanowi główny moduł zarządzający ruchem mikrorobota. Integruje działanie silników oraz czujników odległości, realizując zadania jazdy na wprost, precyzyjnych obrotów oraz jazdy wycentrowanej w korytarzu labiryntu.

## __init__(self, motorR, motorL, sensorR, sensorL, sensorF)
  Konstruktor klasy. Mapuje peryferia robota oraz inicjalizuje zmienne pozycji i stałe kinematyczne kół.
  motorR / motorL: Obiekty klasy Motor odpowiadające za prawy i lewy silnik.
  sensorR / sensorL / sensorF: Obiekty klasy DistanceSensor reprezentujące prawy, lewy i przedni czujnik odległości.
  
## async def rotate_by_90(self, direction)

  Asynchronicznie obraca robota w miejscu o 90 stopni, uruchamiając oba silniki w przeciwnych kierunkach.
  direction: Kierunek obrotu – "L" (w lewo) lub "R" (w prawo).
  
## async def drive(self, distance, direction="F")

  Przemieszcza robota po linii prostej na zadaną odległość.
  distance: Dystans do przejechania przeliczany na stopnie obrotu kół.
  direction: Kierunek jazdy – "F" (w przód, domyślnie) lub "R" (w tył).
  
## async def rotate_by_angle(self, angle, direction)

  Obraca robota w miejscu o precyzyjnie określony kąt przy użyciu obu silników.
  angle: Wartość kąta, o jaki ma obrócić się robot.
  direction: Kierunek obrotu – "L" (w lewo) lub "R" (w prawo).

## async def rotate_by_angle_single(self, angle, direction)

  Obraca robota o zadany kąt, napędzając wyłącznie jedno koło (drugie pozostaje zablokowane).
  angle: Wartość kąta obrotu.
  direction: Kierunek skrętu – "R" (pracuje lewe koło) lub "L" (pracuje prawe koło).

## async def correct_angle_by_movmeant(self)

  Koryguje kąt ustawienia robota względem lewej ściany. Wylicza odchylenie z funkcji trygonometrycznej na podstawie różnicy dwóch pomiarów odległości wykonanych przed i po krótkim podjeździe.

## async def drive_centered_towards_wall_V3(self, distance_to_wall, wall_separation=20, margin=5)

  Realizuje zaawansowaną jazdę do przodu aż do osiągnięcia zadanej odległości od przeszkody przedniej. W pętli co 300 ms wylicza i aplikuje siły korygujące dla silników, bazując na odległości od ścian bocznych (centrowanie) oraz kącie nachylenia robota, zapobiegając odbijaniu się od ścian.
  distance_to_wall: Docelowa odległość od ściany przedniej, przy której robot ma się zatrzymać.
  wall_separation: Szerokość korytarza labiryntu (domyślnie 20 cm).
  margin: Margines błędu tolerancji (domyślnie 5).
