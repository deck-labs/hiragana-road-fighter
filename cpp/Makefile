CXX ?= g++
CXXFLAGS ?= -std=c++17 -O2 -Wall -Wextra
INCLUDES = -I/usr/include/freetype2 -I/usr/include/SDL2
LIBS = -lfreetype -lSDL2 -lpthread -lm

TARGET = road_fighter_cpp
SRC = main.cpp

all: $(TARGET)

$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(SRC) $(LIBS) -o $(TARGET)

clean:
	rm -f $(TARGET)

.PHONY: all clean
