import React, { useState } from "react";
import axios from "axios";
import "./Cashier.css";


const ToppingsList = ["Lettuce -   $0.50", "Tomato  - $0.50", "Cheese - $0.50",];
const SizeList = ["Small", "Medium", "Large"]


const Cashier = () => {
  const [selectedToppings, setSelectedToppings] = useState([]);
  const[selectedSize,setSelectedSize] = useState([]);


  const toggleTopping = (topping) => {
    setSelectedToppings((prevToppings) =>
      prevToppings.includes(topping)
        ? prevToppings.filter((t) => t !== topping)
        : [...prevToppings, topping]
    );
  };


  const toggleSize = (size) => {
    setSelectedSize((prevSize) =>
      prevSize.includes(size)
        ? prevSize.filter((s) => s !== size)
        : [...prevSize, size]
    );
  };




  const handleSubmit = async () => {
   
      const response = await axios.post("http://127.0.0.1:8080/api/order",{
        toppings: selectedToppings,
        fries: selectedSize
      });


      console.log(response.data);
  };




    //alert(`Your selected toppings: ${selectedToppings.join(", ")}`); #might not need this








  return (
    <div className="cashier-container">
      <h2>Cashier Screen</h2>
      <h3> Burger </h3>
      <div className="toppings-section">
        <h4>Select your toppings:</h4>
        {ToppingsList.map((topping) => (
          <div key={topping} className="topping-item">
            <label>
              <input
                type="checkbox"
                checked={selectedToppings.includes(topping)}
                onChange={() => toggleTopping(topping)}
              />
              {topping}
            </label>
          </div>


        ))}
      </div>


      <h5>Fries</h5>
      <div className="size-section"></div>
      {SizeList.map((size) => (
        <div key={size} className="size-item">
          <label>
            <input
              type="checkbox"
              checked={selectedSize.includes(size)}
              onChange={() => toggleSize(size)}
            />
            {size}
          </label>
        </div>
      ))}




      <button onClick={handleSubmit} className="submit-btn">
        Submit Order
      </button>
    </div>
    );
  };


export default Cashier;


