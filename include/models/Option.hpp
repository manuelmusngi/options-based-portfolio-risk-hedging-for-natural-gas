#pragma once
namespace hedging {

class Option {
public:
    enum class Type { ShortPut, LongPut, ShortCall };

    Option(double strike, double premium, Type t);
    virtual ~Option() = default;

    virtual double payoff(double spot) const = 0;

protected:
    double m_k;
    double m_p;
    Type   m_t;
};

}
