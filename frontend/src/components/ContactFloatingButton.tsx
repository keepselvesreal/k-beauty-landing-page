import React, { useState } from 'react';
import InquiryModal from './InquiryModal';
import './ContactFloatingButton.css';

const ContactFloatingButton: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleOpenModal = () => {
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  return (
    <>
      <button
        className="contact-floating-button"
        onClick={handleOpenModal}
        title="관리자에게 문의하기"
        aria-label="Contact Admin"
      >
        <span className="contact-icon">💬</span>
      </button>

      <InquiryModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        inquiryType="customer"
      />
    </>
  );
};

export default ContactFloatingButton;
